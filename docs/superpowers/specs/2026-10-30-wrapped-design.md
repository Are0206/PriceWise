# PriceWise Wrapped: diseño

Fecha: 30 de octubre de 2026 · Estado: aprobado en conversación, pendiente de revisión del documento

## Intención

Un resumen del ahorro de cada usuario al estilo Spotify Wrapped o Rappi Review. En una app real se armaría con un año de compras; como PriceWise es un proyecto académico y no hay tiempo para acumular uso real, **cada lista de compra hace de un "carrito"** y el resumen trata todas las listas del usuario como si fueran su historial del año. El objetivo es mostrar, en la demo, cómo se vería ese resumen después de un año de uso.

Éxito: al recorrer las tarjetas, el usuario entiende cuánto le habría ahorrado PriceWise y termina con ganas de mostrarlo.

## Objetivos

- Un recorrido en formato de historias (una tarjeta a pantalla completa a la vez) con 8 tarjetas.
- Una gráfica con dos líneas acumuladas: lo gastado con PriceWise y lo que se habría gastado sin la app.
- Que casi cualquier lista aporte ahorro con los datos reales actuales.

## No objetivos

- Fechas de compra editables. Las listas conservan su fecha de creación automática; en la demo todas pueden tener la misma fecha y eso es aceptable.
- Compartir o descargar el resumen como imagen.
- Incluir listas de otros usuarios (por ejemplo, listas compartidas por enlace).
- Guardar el resumen: se calcula cada vez que se abre.

## Anti-objetivos (sería un fracaso aunque funcione)

- Cifras que no se puedan explicar. Cada número debe poder reconstruirse desde las listas y los precios actuales.
- Un Wrapped que con datos reales muestre $0 o tarjetas vacías por la regla de cobertura completa de cada lista.
- Una experiencia que no se pueda recorrer con teclado o que ignore "reducir movimiento".

## Cálculo (decidido por Juan)

Base: las listas cuyo dueño es el usuario actual (`ShoppingList.owner = request.user`), ordenadas por `created_at` y luego por `pk`.

Para cada ítem de cada lista, con los precios **actuales** del producto (`Price`):

- **Con PriceWise** = precio más bajo entre los supermercados que venden el producto × cantidad.
- **Sin PriceWise** = precio más alto entre esos mismos supermercados × cantidad.
- **Ahorro del ítem** = sin − con. Es cero cuando el producto solo tiene un precio.
- Un producto **sin ningún precio** no suma a ninguna de las dos líneas ni al ahorro; se cuenta aparte como "productos sin precio".

Esta comparación es **producto por producto**, distinta del "ahorro estimado" del detalle de cada lista (que exige un supermercado con todos los productos). Juan eligió esta regla sabiendo que los totales no coinciden con esa página. La tarjeta del total lleva una frase que explica cómo se calculó.

"Sin PriceWise" se mide contra el **supermercado más caro** (decidido por Juan), no contra el precio promedio.

## Las 8 tarjetas

| # | Tarjeta | Contenido |
|---|---|---|
| 1 | Portada | "Tu año en PriceWise", número de listas y rango de fechas (primera y última lista) |
| 2 | Total ahorrado | Ahorro total en pesos y porcentaje sobre "sin PriceWise"; frase de cómo se calculó |
| 3 | La gráfica | Dos líneas acumuladas lista por lista (eje X: compra 1…n en orden de creación); el área entre ellas es el ahorro |
| 4 | Tu supermercado | El supermercado que ofreció el precio más bajo en más ítems, con cuántos de cuántos; el segundo lugar |
| 5 | Categoría | La categoría con mayor ahorro acumulado y su monto |
| 6 | Producto estrella | El producto con mayor diferencia (más caro − más barato) entre los que el usuario puso en listas, y en cuántas listas aparece |
| 7 | Tus números | Listas, productos distintos, unidades totales, valor promedio por lista (con PriceWise) |
| 8 | Tu perfil | Título según el porcentaje ahorrado y botón "Volver a mis listas" |

Perfiles (mi propuesta, aceptada): menos de 5 % "Comprador tranquilo", de 5 % a 15 % "Buen ojo", más de 15 % "Cazador de ofertas". Los textos exactos quedan a criterio del constructor siempre que mantengan los tres umbrales.

## Dónde se abre (aceptado)

- Página propia en `/lists/wrapped/`, solo para usuarios con sesión.
- Botón "Ver mi Wrapped" en el encabezado del panel de listas.

## Casos borde (aceptados)

- **Sin listas:** una sola tarjeta que invita a crear la primera lista, con enlace a crearla.
- **Una lista:** todo funciona; la tarjeta de la gráfica se reemplaza por "Crea otra lista para ver tu curva".
- **Listas sin productos:** cuentan como lista pero aportan $0.
- **Ningún producto con dos precios:** el ahorro es $0 y el porcentaje 0 %; las tarjetas 4 a 6 muestran un texto que lo explica en vez de un dato vacío.
- **Usuario sin sesión:** redirección al login, como el resto de vistas de listas.

## Experiencia de historias (decidido por Juan)

- Una tarjeta a pantalla completa a la vez.
- Avanza con toque o clic, flechas izquierda y derecha, y barra espaciadora. Escape vuelve a la lista de listas.
- Barras de progreso arriba, una por tarjeta.
- Sin JavaScript, las tarjetas se ven una debajo de otra y todo el contenido es legible.
- Con "reducir movimiento" no hay animaciones, solo el cambio de tarjeta.
- La gráfica sigue las reglas de dataviz del proyecto: dos colores validados, leyenda o etiquetas directas, y la misma información en texto para lectores de pantalla.

## Restricciones

- Django con plantillas y JavaScript vanilla, como el resto del proyecto. Sin librerías nuevas.
- Identidad visual actual: verde, negro y crema, DM Sans y DM Serif Display.
- Rendimiento: una cantidad de consultas que no crezca con el número de listas ni de ítems.
- Coordenadas del SVG con `{% localize off %}` (el idioma `es-co` escribe `72,0`).
- La lógica de cálculo va en `shopping_lists/services.py`, con tests unitarios.

## Decisiones que quedan al constructor

- Textos exactos de cada tarjeta, dentro del tono de la app.
- Colores de las dos líneas, siempre que pasen el validador de paleta y mantengan "con PriceWise" en el verde de la marca.
- Animaciones de transición, si respetan "reducir movimiento".
- Desempates (por ejemplo, dos supermercados con el mismo número de ítems): cualquier regla estable y documentada en el código.

## Decisiones menores tomadas en la revisión (criterio del diseñador)

- **Tarjeta 4:** se cuenta cada ítem de lista (un producto en 3 listas cuenta 3 veces) y solo los productos con dos precios o más. Un empate en el precio más bajo se resuelve por el `pk` del supermercado.
- **Tarjeta 6:** la diferencia es por unidad, sin multiplicar por la cantidad.
- **Tarjeta 7:** el promedio por lista incluye las listas vacías, porque cuentan como lista.
- **Porcentaje:** si "sin PriceWise" suma $0, el porcentaje es 0 %.
- **Paleta:** los colores de la gráfica pasan por el mismo validador de dataviz usado en el historial de precio (`products/services.py`).
- **Datos de la demo:** la base local no tiene listas todavía; las listas de la demo deben incluir productos con precio en varios supermercados (hay 1.495) para que el ahorro se vea.
