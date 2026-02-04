import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { zodToJsonSchema } from 'zod-to-json-schema';
import { authoredLessonSchema } from '../src/shared/authoredLessonSchema';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function main() {
  const schema = zodToJsonSchema(authoredLessonSchema, {
    name: 'AuthoredLesson',
    target: 'jsonSchema7',
    $refStrategy: 'none',
  });

  const outPath = path.resolve(__dirname, '../../backend/shared_schemas/authoredLesson.schema.json');
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(schema, null, 2) + '\n', 'utf-8');

  console.log(`Wrote ${outPath}`);
}

main();
