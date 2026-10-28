/**
 * Crée un compte : node src/cli/create-user.ts <email> "<nom affiché>"
 * Le mot de passe est lu dans la variable d'environnement NEW_USER_PASSWORD (jamais en argument de ligne de commande,
 * où il resterait dans l'historique du shell).
 */
import { loadConfig } from '../config.ts';
import { createPool } from '../db/db.ts';
import { createUser } from '../services/auth-service.ts';

const [email, displayName] = process.argv.slice(2);
const password = process.env['NEW_USER_PASSWORD'];
if (!email || !displayName || !password) {
  console.error('Usage : NEW_USER_PASSWORD=… node src/cli/create-user.ts <email> "<nom affiché>"');
  process.exit(2);
}
const pool = createPool(loadConfig().DATABASE_URL, 2);
try {
  const result = await createUser(pool, { email, displayName, password });
  if (result.ok) console.log(`Compte créé : ${result.user.email} (${result.user.id})`);
  else {
    console.error(
      'Refusé :',
      result.reason,
      'problems' in result ? result.problems.join(', ') : '',
    );
    process.exitCode = 1;
  }
} finally {
  await pool.end();
}
