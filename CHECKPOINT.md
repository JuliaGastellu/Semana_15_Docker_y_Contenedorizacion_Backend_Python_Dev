# Mi revisión del proyecto

Conservé la base de las semanas anteriores y revisé el flujo completo antes del polish.

Corregí la lectura de borradores ajenos por editores, agregué los endpoints de perfil y tags, y protegí la lectura de comentarios de posts privados. También hice que las migraciones creen una base vacía sin depender de carpetas de otras semanas.

En caché comprobé un primer MISS, un segundo HIT y un nuevo MISS después de editar. El recorrido real de registro, login, roles, publicación, comentario y notificación pasó contra PostgreSQL y Redis locales.

Para el polish agregué índices para las referencias y el orden de publicación. Mantengo eager loading de autor, categoría y tags para evitar consultas por cada elemento.

Todavía necesito ampliar las pruebas de los casos límite y medir coverage; lo hago en la semana 14. La cola de tareas sigue siendo local al proceso y el email sigue siendo una simulación, tal como plantea esta fase.
