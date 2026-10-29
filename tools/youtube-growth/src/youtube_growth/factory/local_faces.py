"""Detector-bound portrait crops; a language model never invents coordinates."""
from __future__ import annotations

from pathlib import Path
import hashlib
import io

from .contracts import digest
from .local_models import LocalModelError
from .local_quality import TEXT, object_schema
from .media import fingerprint


def overlap(a, b):
    x, y = max(a[0], b[0]), max(a[1], b[1])
    right, bottom = min(a[0]+a[2], b[0]+b[2]), min(a[1]+a[3], b[1]+b[3])
    intersection = max(0, right-x)*max(0, bottom-y)
    return intersection/(a[2]*a[3]+b[2]*b[3]-intersection)


def portrait_box(face, width, height):
    x, y, w, h = face
    if not 0 <= x < x+w <= width or not 0 <= y < y+h <= height:
        raise ValueError("Visage hors image.")
    side = min(width, height, round(max(w,h)*1.6))
    left = max(0, min(width-side, round(x+w/2-side/2)))
    top = max(0, min(height-side, round(y+h/2-side/2)))
    if not (left <= x and top <= y and left+side >= x+w and top+side >= y+h):
        raise ValueError("Le cadrage doit conserver le visage entier.")
    return [left, top, side, side]


def face_proposals(frame):
    try:
        import cv2
    except ImportError as error:
        raise LocalModelError("opencv_dependency_missing") from error
    image = cv2.imread(frame["path"])
    if image is None:
        raise LocalModelError("local_thumbnail_frame_unreadable")
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    detections, detectors = [], []
    for name in ("haarcascade_frontalface_default.xml", "haarcascade_frontalface_alt2.xml"):
        path = Path(cv2.data.haarcascades) / name
        detector = cv2.CascadeClassifier(str(path))
        if detector.empty():
            raise LocalModelError("local_thumbnail_detector_missing")
        rows = detector.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=4, minSize=(16,16))
        detections.append([list(map(int, row)) for row in rows])
        detectors.append({"name": name, "sha256": fingerprint(path)})
    # Require agreement: decorative elements in slides can fool a single cascade.
    faces = [face for face in detections[0] if any(overlap(face, other) >= .35 for other in detections[1])]
    faces.sort(key=lambda face: (-face[2]*face[3], face[0], face[1]))
    if not faces:
        raise LocalModelError("local_thumbnail_face_not_detected")
    proof = {"version": 2, "opencv_version": cv2.__version__, "detectors": detectors,
             "frame": frame, "scope": "frontal_face_consensus_not_identity_or_emotion"}
    return [{"face_box": face, "crop_pixels": portrait_box(face,width,height), "image_size": [width,height]} for face in faces], proof


def choose_portrait(model, frame):
    from PIL import Image
    proposals, detection = face_proposals(frame)
    proposals = proposals[:model.options["maximum_images_per_call"]]
    images, choices = [], []
    for index, proposal in enumerate(proposals):
        key = digest({"detection": detection, "proposal": proposal})
        path = Path(frame["path"]).parent / "face-crops" / (key+".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        x, y, w, h = proposal["crop_pixels"]
        with Image.open(frame["path"]) as source:
            crop = source.crop((x,y,x+w,y+h))
            pixels = io.BytesIO()
            crop.save(pixels, format="PNG")
        expected = hashlib.sha256(pixels.getvalue()).hexdigest()
        if path.exists() and fingerprint(path) != expected:
            raise LocalModelError("local_thumbnail_crop_changed")
        if not path.exists():path.write_bytes(pixels.getvalue())
        images.append(path)
        choices.append({"index": index, **proposal, "path": str(path), "sha256": expected})
    schema = object_schema({"index": {"enum": list(range(len(choices)))}, "usable": {"type": "boolean"}, "reason": TEXT})
    answer, evidence = model.complete("thumbnail_crop_selection",
        "Examine ces cadrages réels d'une même image de podcast, dans l'ordre des indices. "
        "Choisis un portrait net, avec le visage ENTIER, sans coupure des yeux ou de la bouche et sans autre visage partiel. "
        "Préfère une expression naturelle, les yeux ouverts quand ils sont visibles. Une affiche ou un objet qui ressemble à un visage ne convient pas. "
        "Le portrait illustre seulement la discussion ; ne prétends identifier le nom, l'émotion ou une réaction à une phrase. "
        "Les coordonnées sont déjà fixées par les détecteurs ; choisis uniquement un index. Si aucun portrait n'est utilisable, usable=false.",
        {"choices": [{k:v for k,v in row.items() if k not in {"path","sha256"}} for row in choices], "detection": detection},
        schema, images=images, reviewer=True)
    if not answer["usable"]:
        raise LocalModelError("local_thumbnail_face_not_usable")
    selected = choices[answer["index"]]
    x,y,w,h = selected["crop_pixels"]
    width,height = selected["image_size"]
    return [x/width,y/height,w/width,h/height], {"detection": detection, "choices": choices, "selection": answer, "evidence": evidence}
