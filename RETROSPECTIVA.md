# Mi retrospectiva 4Ls

## Lo que me gustó

Me resultó útil ver cómo se conectan las capas: una validación evita una escritura incorrecta, un commit habilita la invalidación y un evento llega al navegador.

## Lo que aprendí

Aprendí que probar un endpoint aislado no alcanza. Necesito probar identidad, permisos, estado persistido y caché dentro del mismo recorrido.

## Lo que me faltó

Me faltó preparar antes un entorno repetible para PostgreSQL y Redis. También necesito automatizar más casos de error y medir la cobertura.

## Lo que quiero seguir trabajando

Quiero consolidar las pruebas de integración y empaquetar el proyecto para ejecutarlo con un solo comando.
