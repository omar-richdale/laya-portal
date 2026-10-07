// Swagger is served locally so documentation still works with the network disconnected.
import {mkdirSync, copyFileSync} from 'node:fs';
const target = new URL('../public/api-docs/', import.meta.url);
mkdirSync(target, {recursive:true});
for (const file of ['swagger-ui-bundle.js','swagger-ui.css','LICENSE']) {
  copyFileSync(new URL('../node_modules/swagger-ui-dist/'+file, import.meta.url), new URL(file,target));
}
