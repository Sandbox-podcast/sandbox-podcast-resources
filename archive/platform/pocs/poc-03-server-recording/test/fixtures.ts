/**
 * Sorties `ffprobe -of json` construites à la main pour tester le parseur.
 * Ce ne sont pas des mesures : les valeurs sont choisies pour couvrir les cas.
 */
export const videoProbe = {
  streams: [
    {
      codec_type: 'video',
      codec_name: 'h264',
      width: 1920,
      height: 1080,
      avg_frame_rate: '30/1',
    },
  ],
  format: {
    format_name: 'mov,mp4,m4a,3gp,3g2,mj2',
    duration: '60.033000',
    size: '30000000',
    bit_rate: '4000000',
  },
};

export const audioProbe = {
  streams: [{ codec_type: 'audio', codec_name: 'opus' }],
  format: { format_name: 'ogg', duration: '59.980000', size: '480000', bit_rate: '64000' },
};
