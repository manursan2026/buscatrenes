# -*- coding: utf-8 -*-
"""Manual de usuario de BuscaTrenes (PDF con reportlab, capturas del emulador en manual/)."""
import os, re, datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle,
                                PageBreak, KeepTogether, NextPageTemplate, ListFlowable, ListItem)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage

S = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(S, "manual")
OUT = os.path.join(S, "Manual_BuscaTrenes.pdf")
VERSION = re.search(r'versionName="([^"]+)"', open(os.path.join(S, "android_buscador", "AndroidManifest.xml")).read()).group(1)
DATA_FECHA = re.search(r'const DATA_FECHA = "(\d{4}-\d{2}-\d{2})"', open(os.path.join(S, "buscador_trenes.html")).read()).group(1)
DATA_FECHA_TXT = "%s/%s/%s" % (DATA_FECHA[8:10], DATA_FECHA[5:7], DATA_FECHA[0:4])

F = "/System/Library/Fonts/Supplemental/"
pdfmetrics.registerFont(TTFont("Arial", F + "Arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", F + "Arial Bold.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Italic", F + "Arial Italic.ttf"))
pdfmetrics.registerFont(TTFont("Arial-BoldItalic", F + "Arial Bold Italic.ttf"))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic", boldItalic="Arial-BoldItalic")

AZUL = colors.HexColor("#2F6BFF"); OSCURO = colors.HexColor("#0F172A"); CIAN = colors.HexColor("#38BDF8")
VERDE = colors.HexColor("#1E8E4E"); NARANJA = colors.HexColor("#FF7A1A"); ROJO = colors.HexColor("#E5484D")
TINTA = colors.HexColor("#1B1F2B"); GRIS = colors.HexColor("#555C6E"); SUAVE = colors.HexColor("#EEF2FA"); LINEA = colors.HexColor("#D5DAE6")

st = {
    "title": ParagraphStyle("title", fontName="Arial-Bold", fontSize=30, leading=36, textColor=colors.white),
    "subtitle": ParagraphStyle("subtitle", fontName="Arial", fontSize=14, leading=18, textColor=colors.white),
    "h1": ParagraphStyle("h1", fontName="Arial-Bold", fontSize=20, leading=24, textColor=AZUL, spaceBefore=6, spaceAfter=10),
    "h2": ParagraphStyle("h2", fontName="Arial-Bold", fontSize=13.5, leading=17, textColor=TINTA, spaceBefore=12, spaceAfter=5, keepWithNext=1),
    "body": ParagraphStyle("body", fontName="Arial", fontSize=9.8, leading=13.5, textColor=TINTA, alignment=TA_JUSTIFY, spaceAfter=5),
    "bullet": ParagraphStyle("bullet", fontName="Arial", fontSize=9.8, leading=13.5, textColor=TINTA, leftIndent=0, spaceAfter=2),
    "cap": ParagraphStyle("cap", fontName="Arial-Italic", fontSize=8, leading=10, textColor=GRIS, alignment=TA_CENTER),
    "note": ParagraphStyle("note", fontName="Arial", fontSize=9.2, leading=12.5, textColor=TINTA),
    "toc1": ParagraphStyle("toc1", fontName="Arial-Bold", fontSize=10.5, leading=15, textColor=TINTA),
    "toc2": ParagraphStyle("toc2", fontName="Arial", fontSize=9.5, leading=13, textColor=GRIS, leftIndent=14),
    "cell": ParagraphStyle("cell", fontName="Arial", fontSize=8.8, leading=11.5, textColor=TINTA),
    "cellb": ParagraphStyle("cellb", fontName="Arial-Bold", fontSize=8.8, leading=11.5, textColor=TINTA),
    "mono": ParagraphStyle("mono", fontName="Courier", fontSize=8.6, leading=11, textColor=TINTA, leftIndent=10, spaceAfter=5),
}

def P(t, s="body"): return Paragraph(t, st[s])

def bullets(items):
    return ListFlowable([ListItem(Paragraph(i, st["bullet"]), leftIndent=12, value="•") for i in items],
                        bulletType="bullet", start="•", leftIndent=12, bulletFontName="Arial", bulletFontSize=9)

def shot(name, w=5.6*cm, crop=None):
    """Captura a la anchura indicada. crop=(y0,y1) en px del original (1080x2400) para recortar en vertical."""
    im = PILImage.open(os.path.join(M, name + ".png")).convert("RGB")
    if crop:
        im = im.crop((0, crop[0], im.width, crop[1]))
    if im.width > 640:
        im = im.resize((640, int(im.height * 640 / im.width)), PILImage.LANCZOS)
    path = os.path.join(M, "_emb_" + name + ("_%d_%d" % crop if crop else "") + ".jpg"); im.save(path, quality=88)
    return Image(path, width=w, height=w * im.height / im.width)

def figrow(items, w=5.6*cm):
    """Fila de capturas con pie: items = [(nombre, pie, crop?), ...]"""
    imgs, caps = [], []
    for it in items:
        crop = it[2] if len(it) > 2 else None
        imgs.append(shot(it[0], w, crop)); caps.append(Paragraph(it[1], st["cap"]))
    t = Table([imgs, caps], colWidths=[w + 0.5*cm] * len(items), hAlign="CENTER")
    t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, 0), "TOP"),
                           ("TOPPADDING", (0, 1), (-1, 1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return KeepTogether([Spacer(1, 4), t])

def note(text, color=AZUL, title="Nota"):
    t = Table([[Paragraph("<b>%s</b>  %s" % (title, text), st["note"])]], colWidths=[16.4*cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), SUAVE), ("LINEBEFORE", (0, 0), (0, -1), 3, color),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return KeepTogether([Spacer(1, 3), t, Spacer(1, 6)])

def table(rows, widths):
    data = [[Paragraph(c, st["cellb" if i == 0 else "cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, LINEA), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BACKGROUND", (0, 0), (-1, 0), SUAVE),
                           ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t

class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=2.3*cm, rightMargin=2.3*cm, topMargin=2.2*cm, bottomMargin=2*cm,
                         title="BuscaTrenes · Manual de usuario", author="BuscaTrenes", **kw)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="cover", frames=[frame], onPage=self.cover),
                               PageTemplate(id="normal", frames=[frame], onPage=self.decorate)])
    def cover(self, canv, doc):
        canv.saveState()
        canv.setFillColor(OSCURO); canv.rect(0, A4[1] - 11*cm, A4[0], 11*cm, fill=1, stroke=0)
        canv.setFillColor(AZUL); canv.rect(0, A4[1] - 11.4*cm, A4[0], 0.4*cm, fill=1, stroke=0)
        # tren estilizado: dos vagones y una vía
        x, y = A4[0] - 6.2*cm, A4[1] - 3.4*cm
        canv.setStrokeColor(CIAN); canv.setLineWidth(1.6)
        canv.line(x - 0.4*cm, y - 0.65*cm, x + 4.2*cm, y - 0.65*cm)
        canv.setFillColor(colors.white)
        canv.roundRect(x, y - 0.4*cm, 1.7*cm, 1.1*cm, 0.18*cm, fill=1, stroke=0)
        canv.roundRect(x + 1.9*cm, y - 0.4*cm, 1.7*cm, 1.1*cm, 0.18*cm, fill=1, stroke=0)
        canv.setFillColor(AZUL)
        for dx in (0.22, 0.72, 1.22, 2.12, 2.62, 3.12):
            canv.rect(x + dx*cm, y + 0.12*cm, 0.34*cm, 0.34*cm, fill=1, stroke=0)
        canv.setFillColor(OSCURO)
        for dx in (0.35, 1.25, 2.25, 3.15):
            canv.circle(x + dx*cm, y - 0.45*cm, 0.13*cm, fill=1, stroke=0)
        canv.restoreState()
    def decorate(self, canv, doc):
        canv.saveState()
        canv.setStrokeColor(LINEA); canv.setLineWidth(0.5)
        canv.line(doc.leftMargin, A4[1] - 1.5*cm, A4[0] - doc.rightMargin, A4[1] - 1.5*cm)
        canv.setFont("Arial", 8); canv.setFillColor(GRIS)
        canv.drawString(doc.leftMargin, A4[1] - 1.35*cm, "BuscaTrenes · Manual de usuario")
        canv.drawRightString(A4[0] - doc.rightMargin, A4[1] - 1.35*cm, "Versión %s · horarios del %s" % (VERSION, DATA_FECHA_TXT))
        canv.drawCentredString(A4[0] / 2, 1.2*cm, str(doc.page))
        canv.restoreState()
    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph):
            if fl.style.name == "h1":
                key = "h1-%s" % self.seq.nextf("h1"); self.canv.bookmarkPage(key)
                self.notify("TOCEntry", (0, fl.getPlainText(), self.page, key))
            elif fl.style.name == "h2":
                key = "h2-%s" % self.seq.nextf("h2"); self.canv.bookmarkPage(key)
                self.notify("TOCEntry", (1, fl.getPlainText(), self.page, key))

def H1(t): return [PageBreak(), P(t, "h1")]
def H2(t): return [P(t, "h2")]

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
hoy = datetime.date.today()
FECHA_LARGA = "%s %d" % (MESES[hoy.month - 1].capitalize(), hoy.year)

story = []
# ---------- Portada ----------
story += [Spacer(1, 2.2*cm), P("BuscaTrenes", "title"), Spacer(1, 0.3*cm),
          P("Manual de usuario", "subtitle"), Spacer(1, 0.2*cm),
          P("Buscador de trenes para Android: horarios de RENFE, OUIGO, FGC, Euskotren y SFM Mallorca, con transbordos, "
            "salidas por estación, incidencias y seguimiento del viaje", "subtitle"),
          NextPageTemplate("normal"), Spacer(1, 4.4*cm)]
cover_tbl = Table([[shot("01_inicio", 4.4*cm), shot("05_resultados", 4.4*cm), shot("09_seguimiento", 4.4*cm)]], colWidths=[5.2*cm]*3, hAlign="CENTER")
cover_tbl.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
story += [cover_tbl, Spacer(1, 0.8*cm),
          Paragraph("Versión %s · %s · Capturas tomadas en el emulador de Android con los horarios extraídos el %s." % (VERSION, FECHA_LARGA, DATA_FECHA_TXT), st["cap"])]

# ---------- Índice ----------
toc = TableOfContents(); toc.levelStyles = [st["toc1"], st["toc2"]]; toc.dotsMinLevel = 0
st["h1toc"] = ParagraphStyle("h1toc", parent=st["h1"])
story += [PageBreak(), P("Índice", "h1toc"), toc]

# ---------- 1. Introducción ----------
story += H1("1. Introducción")
story += [P("<b>BuscaTrenes</b> es una aplicación para Android que responde a una pregunta sencilla: <b>¿qué trenes hay entre dos estaciones "
            "en una fecha y a partir de una hora?</b> Busca primero trenes directos y, si no los hay, construye automáticamente enlaces con "
            "uno o dos transbordos respetando el tiempo mínimo de enlace que tú decidas."),
          P("Combina en un único buscador los horarios oficiales de <b>RENFE</b> (alta velocidad, larga distancia, media distancia y Cercanías), "
            "<b>OUIGO</b>, <b>FGC</b> (Ferrocarrils de la Generalitat de Catalunya), <b>Euskotren</b> y <b>SFM Mallorca</b>. Todos esos horarios "
            "van <b>dentro de la aplicación</b>, así que la búsqueda funciona sin conexión: en un túnel, en el campo o en modo avión."),
          P("Además de buscar trayectos, la aplicación muestra el panel de <b>salidas</b> de cualquier estación, localiza un tren por su "
            "<b>número</b>, avisa de las <b>incidencias</b> que publican los operadores y permite <b>seguir tu viaje</b> en tiempo real con el "
            "retraso oficial de RENFE o, en su defecto, el que se estima con el GPS del teléfono.")]
story += H2("1.1 Requisitos")
story += [bullets(["Teléfono o tablet con <b>Android 7.0</b> o superior.",
                   "Unos 4 MB de espacio. No necesita cuenta de usuario ni registro.",
                   "Conexión a Internet <b>solo</b> para las incidencias y los retrasos en tiempo real; buscar trenes funciona sin red.",
                   "Permiso de <b>ubicación</b>, opcional: sirve para el botón <i>Usar mi ubicación</i>, para las incidencias de tu zona y para el seguimiento por GPS."])]
story += H2("1.2 Cómo está organizado este manual")
story += [P("El capítulo 2 explica cómo instalar la aplicación. El 3 presenta la pantalla principal. Los capítulos 4 a 9 recorren cada función: "
            "buscar un trayecto, las acciones sobre un tren, el seguimiento del viaje, las salidas por estación, la búsqueda por número y las "
            "incidencias. El capítulo 10 describe de dónde salen los datos y cuándo caducan, y el 11 responde a las preguntas más frecuentes.")]

# ---------- 2. Instalación ----------
story += H1("2. Instalación y primer arranque")
story += H2("2.1 Instalar el APK en el teléfono")
story += [P("La aplicación se distribuye como un fichero <b>buscador_trenes.apk</b> (no está en Google Play). Para instalarlo:"),
          bullets(["Descarga o copia el fichero al dispositivo (desde la página web de descargas con el navegador del móvil, por cable USB, correo, Drive…).",
                   "Ábrelo desde la notificación de descarga o con la aplicación <i>Archivos</i>.",
                   "Android pedirá permiso para <i>instalar aplicaciones desconocidas</i> a la aplicación desde la que lo abres (Chrome, Archivos…). Concédelo una vez.",
                   "Pulsa <b>Instalar</b>. Si ya tenías una versión anterior, se actualiza encima y conserva tus trayectos favoritos."]),
          note("Cada nueva versión del APK lleva horarios más recientes. Cuando la aplicación detecte que sus horarios tienen más de dos meses, "
               "mostrará un aviso en la parte superior recomendando actualizar.", NARANJA, "Aviso"),
          figrow([("16_icono_marcado", "Icono de BuscaTrenes en el cajón de aplicaciones"), ("01_inicio", "Pantalla inicial tras abrir la aplicación")], 6.2*cm)]
story += H2("2.2 Probar la aplicación en el emulador")
story += [P("Si tienes un Mac con Android Studio instalado, en la carpeta del proyecto encontrarás <b>Abrir_Emulador.command</b>: con doble clic "
            "arranca el emulador de Android, instala el APK más reciente y abre BuscaTrenes, sin necesidad de un teléfono.")]

# ---------- 3. Pantalla principal ----------
story += H1("3. La pantalla principal")
story += [P("Al abrir la aplicación se cargan los horarios (un par de segundos) y aparece la pantalla de búsqueda. De arriba abajo:"),
          bullets(["<b>Aviso de datos</b> (solo si los horarios tienen más de dos meses).",
                   "<b>Panel de seguimiento</b> (solo mientras sigues un viaje; capítulo 6).",
                   "<b>Pestañas</b>: <i>Trayecto</i>, <i>Salidas</i>, <i>Nº tren</i> y, cuando hay incidencias publicadas, <i>Incidencias</i>.",
                   "La <b>tarjeta</b> de la pestaña activa con su formulario.",
                   "Los <b>resultados</b> de la última búsqueda y, al final, la fecha en la que se extrajeron los horarios."]),
          figrow([("01_inicio", "Pestaña Trayecto"), ("13_salidas", "Pestaña Salidas"), ("15_incidencias", "Pestaña Incidencias")])]

# ---------- 4. Buscar un trayecto ----------
story += H1("4. Buscar un trayecto")
story += H2("4.1 Origen y destino")
story += [P("Escribe parte del nombre de la estación en <b>Origen</b> y elige una de las sugerencias. No hace falta poner acentos ni "
            "mayúsculas: <i>madrid</i> muestra Chamartín, Atocha Cercanías, Puerta de Atocha, Nuevos Ministerios, Recoletos y Príncipe Pío. "
            "Se listan primero las estaciones que <i>empiezan</i> por lo escrito y después las que lo contienen. Repite con <b>Destino</b>."),
          P("Cuando dos operadores llaman de forma distinta a la misma estación física (por ejemplo, <i>MADRID-PUERTA DE ATOCHA</i> de OUIGO y "
            "<i>Madrid-Puerta de Atocha-Almudena Grandes</i> de RENFE) la aplicación las trata como una sola, así que basta con elegir cualquiera "
            "de los nombres para ver los trenes de todos los operadores."),
          figrow([("02_autocompletar", "Sugerencias al escribir «madrid»"), ("03_formulario", "Formulario completo listo para buscar")])]
story += H2("4.2 Usar mi ubicación")
story += [P("El botón <b>Usar mi ubicación</b> rellena el origen con la estación más cercana al lugar donde estás e indica a qué distancia queda. "
            "La primera vez Android pide permiso de ubicación: elige <i>Mientras se usa la aplicación</i>. Si lo deniegas, el resto de la "
            "aplicación sigue funcionando; solo dejan de estar disponibles este botón, las incidencias de «Mi zona» y la estimación de retraso por GPS."),
          figrow([("10_permiso", "Permiso de ubicación (solo la primera vez)"), ("11_ubicacion", "Estación más cercana localizada", (0, 1900))])]
story += H2("4.3 Fecha, hora y tiempo de enlace")
story += [bullets(["<b>Fecha</b>: por defecto hoy. Puedes elegir cualquier día dentro de la vigencia de los horarios (los trenes solo aparecen "
                   "si circulan ese día de la semana y esa fecha está dentro del periodo que publica el operador).",
                   "<b>Hora</b>: se muestran los trenes que salen a partir de esa hora. Por defecto es la hora actual.",
                   "<b>Ver todo el día</b>: ignora la hora y lista todos los trenes del día, ordenados por hora de salida.",
                   "<b>Enlace mín. (min)</b>: tiempo mínimo que exiges entre la llegada de un tren y la salida del siguiente en un transbordo "
                   "(10 minutos por defecto). Si el cambio es a pie entre dos estaciones próximas se añaden 10 minutos más. Entre dos líneas de "
                   "Cercanías, con el valor por defecto, también se ofrecen enlaces más ajustados: 5 minutos en la misma estación y 7,5 andando a otra cercana.",
                   "<b>Guardar trayecto como favorito</b>: al buscar, el par origen → destino queda guardado como un acceso rápido (apartado 4.6)."]),
          P("Pulsa <b>Buscar trenes</b>. El botón está desactivado mientras se cargan los horarios y hasta que origen y destino son estaciones válidas.")]
story += H2("4.4 Trenes directos")
story += [P("Si hay trenes directos, la cabecera indica cuántos y, cuando intervienen varios tipos de servicio, aparecen <b>filtros</b> "
            "(Alta Velocidad, OUIGO, Media Distancia, Cercanías…): toca uno para ocultar o volver a mostrar esos trenes. Cada tarjeta muestra:"),
          bullets(["La <b>categoría</b> (AV, LD, MD, CER, OUIGO, FGC, EUSKO, SFM), el <b>número de tren</b> y la <b>línea o producto</b> (AVE, Madrid C5, REGIONAL…). "
                   "FGC, Euskotren y SFM no publican número de tren: en su lugar se muestra «Servicio».",
                   "Hora de salida y de llegada en las estaciones elegidas y la <b>duración</b>.",
                   "Los días en que <b>circula</b> y la <b>vigencia</b> del horario, más el recorrido completo del tren (puede empezar antes de tu origen y terminar después de tu destino).",
                   "<b>Paradas intermedias</b>: toca la línea para desplegar la lista con la hora de llegada y salida de cada una.",
                   "Las <b>incidencias</b> que afectan a esa línea o a alguna de sus estaciones (recuadros amarillos), si las hay.",
                   "Los botones <b>Seguir</b>, <b>calendario</b> y <b>Compartir</b> (capítulo 5)."]),
          figrow([("05_resultados", "44 trenes directos Madrid → Barcelona"), ("06_filtro", "Filtro OUIGO desactivado"), ("07_paradas", "Paradas intermedias desplegadas")])]
story += H2("4.5 Enlaces con transbordo")
story += [P("Cuando no hay tren directo, la aplicación busca automáticamente combinaciones con <b>un transbordo</b> y, si tampoco las hay, con <b>dos</b>. "
            "La cabecera lo indica («Sin trenes directos. 19 opción(es) con 1 transbordo») y cada tarjeta encadena los trenes con un recuadro azul "
            "<b>Transbordo en …</b> que muestra la estación de cambio y los minutos de espera. Si el cambio es entre dos estaciones distintas pero "
            "próximas (por ejemplo, Atocha Cercanías y Puerta de Atocha) se indica que el enlace es a pie."),
          P("Al pie de cada combinación figura la <b>duración total</b> del viaje y los mismos botones que en un tren directo; <i>Seguir</i> hace el "
            "seguimiento de todos los tramos, avisando de cada transbordo."),
          figrow([("12_transbordo", "Fuenlabrada → Alcalá de Henares: Cercanías C5 + C7 con cambio en Atocha")], 7.4*cm)]
story += H2("4.6 Trayectos favoritos")
story += [P("Marca <b>Guardar trayecto como favorito</b> antes de buscar y el par origen → destino aparecerá como un <b>chip azul</b> encima del "
            "formulario. Tocar el chip rellena origen y destino y lanza la búsqueda con la fecha y hora actuales; la <b>X</b> de la derecha lo borra. Se conservan "
            "hasta ocho favoritos, los más recientes primero, y sobreviven a las actualizaciones de la aplicación."),
          figrow([("04_favorito", "Chip del trayecto favorito Madrid → Barcelona", (0, 1200))], 7.0*cm)]

# ---------- 5. Acciones ----------
story += H1("5. Acciones sobre un tren")
story += [P("Al pie de cada resultado hay tres botones:"),
          table([["Botón", "Qué hace"],
                 ["Seguir", "Inicia el seguimiento del viaje: cuenta atrás hasta la salida, croquis de la ruta, posición y retraso del tren (capítulo 6)."],
                 ["Calendario", "Abre el editor de eventos de tu aplicación de calendario con el trayecto ya rellenado (título, horas y descripción). "
                                     "Tú revisas y guardas el evento; BuscaTrenes no escribe en el calendario por su cuenta."],
                 ["Compartir", "Abre el panel de compartir de Android con un resumen de texto del itinerario (fecha, tren, estaciones, horas y duración) "
                                  "para enviarlo por WhatsApp, correo, mensajes… o copiarlo al portapapeles."]],
                [3.4*cm, 13.0*cm]),
          figrow([("08_compartir", "Panel de compartir con el resumen del tren 03301")], 6.4*cm)]

# ---------- 6. Seguimiento ----------
story += H1("6. Seguimiento del viaje")
story += [P("Pulsa <b>Seguir</b> en el tren (o combinación) que vas a tomar. Aparece un panel azul fijo en la parte superior de la pantalla que se "
            "actualiza solo cada medio minuto y acompaña todo el viaje. Solo se puede seguir un viaje a la vez; empezar otro sustituye al anterior."),
          figrow([("09_seguimiento", "Panel de seguimiento antes de la salida: cuenta atrás y croquis de la ruta")], 7.4*cm)]
story += H2("6.1 Qué muestra el panel")
story += [bullets(["<b>Antes de salir</b>: «Sale a las 19:34 · faltan 31 min», con la hora de llegada prevista al destino.",
                   "<b>En marcha</b>: la próxima parada y la hora estimada de llegada, la lista de las siguientes paradas y, si hay transbordos, "
                   "la estación de cambio, el tren siguiente y el tiempo de espera que queda.",
                   "<b>Croquis de la ruta</b>: las estaciones del recorrido unidas por la línea; el punto grande marca dónde está el tren.",
                   "<b>Retraso</b>: «~5 min de retraso (Renfe)» cuando el operador lo publica en tiempo real; si no, «~5 min de retraso según "
                   "tu posición GPS» una vez que la aplicación ha comprobado que vas montado en el tren.",
                   "<b>Dejar de seguir</b> termina el seguimiento en cualquier momento."])]
story += H2("6.2 Cómo se estima el retraso")
story += [P("RENFE publica en abierto la posición y el retraso de muchos de sus trenes. Cuando hay conexión y el dato existe, se muestra como "
            "<i>retraso oficial</i>. Si no hay dato, la aplicación compara tu posición GPS con el punto de la ruta por el que el tren debería pasar "
            "en ese momento: la diferencia de tiempo es el retraso estimado. Para no dar por buena una lectura desde el andén, antes de mostrarlo "
            "espera a detectar que te mueves a velocidad de tren; el valor se suaviza y los saltos grandes (túneles, cruces de vías) solo se aceptan si se repiten."),
          P("Si durante un minuto estás a más de 5 km de la ruta, o si el tren debería avanzar y tu posición no lo hace, el panel pregunta "
            "<b>«¿Desea continuar realizando el seguimiento?»</b>: responde <i>Sí</i> para mantenerlo (no volverá a preguntar) o <i>No</i> para pararlo. "
            "El seguimiento termina solo dos horas después de la llegada prevista."),
          note("Con la pantalla apagada Android no entrega posiciones GPS a la aplicación; al volver a encenderla el panel se pone al día en unos segundos. "
               "Mientras el tren está en marcha la aplicación pide mantener la pantalla encendida si el sistema lo permite.", AZUL, "Consejo")]

# ---------- 7. Salidas ----------
story += H1("7. Salidas por estación")
story += [P("La pestaña <b>Salidas</b> funciona como el panel de una estación: elige la estación (o usa tu ubicación), la fecha y la hora desde la que "
            "quieres ver salidas y pulsa <b>Ver salidas</b>. Se listan hasta 40 trenes en orden de salida con la hora, la categoría, el destino final "
            "del tren y su línea. Cuando RENFE publica el retraso de un tren, aparece junto a la hora."),
          P("<b>Toca una salida</b> para abrirla en la pestaña Trayecto: se rellena el origen con la estación y el destino con el final del tren, y se "
            "muestra la tarjeta completa con paradas, incidencias y botones."),
          figrow([("13_salidas", "267 salidas desde Madrid-Atocha Cercanías a partir de las 18:59")], 7.0*cm)]

# ---------- 8. Nº tren ----------
story += H1("8. Búsqueda por número de tren")
story += [P("Si conoces el número del tren (figura en el billete y en los paneles de la estación), escríbelo en la pestaña <b>Nº tren</b> y pulsa "
            "<b>Buscar tren</b>. Los ceros a la izquierda no importan: <i>3309</i> y <i>03309</i> dan el mismo resultado. Se muestran todas las "
            "circulaciones con ese número vigentes en la fecha elegida en Trayecto —un mismo número puede tener variantes de recorrido según el "
            "día— con sus paradas ya desplegadas."),
          note("FGC, Euskotren y SFM Mallorca no publican números de tren, así que esta búsqueda solo encuentra trenes de RENFE y OUIGO.", GRIS),
          figrow([("14_numero_tren", "Tren 03309: dos variantes (hasta Figueres y hasta Barcelona)")], 7.0*cm)]

# ---------- 9. Incidencias ----------
story += H1("9. Incidencias en tiempo real")
story += [P("Al arrancar, si hay conexión, la aplicación descarga las incidencias que publican los operadores (obras, cortes, servicios alternativos, "
            "ascensores fuera de servicio…). Si hay alguna, aparece la pestaña <b>Incidencias</b>; si no hay ninguna o no hay red, la pestaña se oculta. "
            "Las incidencias se refrescan cada dos minutos mientras la pestaña está abierta."),
          bullets(["<b>Ámbito</b>: <i>Mi zona</i> (estaciones a menos de 50 km de tu posición; requiere ubicación), una provincia o comunidad autónoma, o <i>Toda España</i>.",
                   "<b>Línea</b>: filtra por una línea concreta de las que hay en el ámbito elegido.",
                   "Cada incidencia indica la categoría y la línea afectada y el texto tal como lo publica el operador."]),
          P("Las mismas incidencias se muestran también <b>dentro de cada resultado</b> de búsqueda al que afectan (recuadros amarillos), "
            "de modo que no hace falta consultar la pestaña para enterarse."),
          figrow([("15_incidencias", "Nueve incidencias en la zona de Madrid"), ("12_transbordo", "Incidencias dentro de un resultado")])]

# ---------- 10. Datos ----------
story += H1("10. Los datos: de dónde salen y cuándo caducan")
story += [P("Los horarios proceden de los ficheros <b>GTFS</b> que los operadores publican en abierto (RENFE en su web, FGC en la suya, y OUIGO, "
            "Euskotren y SFM Mallorca a través del Punto de Acceso Nacional de transporte). Se descargan, se combinan y se comprimen dentro de la "
            "aplicación al generar cada versión; la fecha de esa extracción figura al pie de la pantalla."),
          table([["Operador", "Servicios incluidos", "Observaciones"],
                 ["RENFE", "AVE, Avlo, Alvia, Euromed, Intercity, larga y media distancia, Regionales y todos los núcleos de Cercanías",
                  "Con retraso y posición en tiempo real cuando hay red"],
                 ["OUIGO", "Alta velocidad Madrid–Barcelona, Valencia, Alicante, Andalucía…", "Número de tren disponible"],
                 ["FGC", "Líneas metropolitanas y comarcales de Barcelona y Lleida", "Sin número de tren («Servicio»)"],
                 ["Euskotren", "Líneas de Bizkaia y Gipuzkoa", "Sin número de tren"],
                 ["SFM Mallorca", "Líneas de Serveis Ferroviaris de Mallorca", "Sin número de tren"]],
                [2.6*cm, 8.2*cm, 5.6*cm]),
          Spacer(1, 6),
          P("Cada horario tiene un <b>periodo de vigencia</b> (normalmente de unas semanas a unos meses). Si buscas una fecha fuera de ese periodo "
            "el tren no aparece, aunque en la realidad exista con un horario más reciente. Por eso conviene <b>actualizar la aplicación</b> "
            "periódicamente: cada versión nueva incorpora los horarios vigentes en ese momento, y el aviso de la parte superior lo recuerda cuando "
            "los datos tienen más de dos meses.")]
story += H2("10.1 Limitaciones conocidas")
story += [bullets(["<b>IRYO</b> no publica sus horarios en formato abierto y por tanto no está incluido.",
                   "Los metros, tranvías y funiculares urbanos se han dejado fuera a propósito: la aplicación está pensada para trayectos ferroviarios interurbanos.",
                   "Los calendarios se simplifican a un patrón semanal: las excepciones por festivos concretos que publican algunos operadores no se tienen en cuenta.",
                   "Los transbordos se buscan hasta dos niveles; no se ofrecen combinaciones de tres o más trenes.",
                   "El retraso oficial en tiempo real solo está disponible para los trenes de RENFE que el operador publica."])]

# ---------- 11. FAQ ----------
story += H1("11. Preguntas frecuentes")
faq = [("No aparece ningún tren para una fecha de dentro de dos meses.",
        "Probablemente esa fecha queda fuera de la vigencia de los horarios embebidos. Comprueba la fecha de extracción al pie de la pantalla e instala la versión más reciente de la aplicación."),
       ("El botón «Buscar trenes» está gris.",
        "Espera a que terminen de cargarse los horarios (el botón muestra «Cargando datos…») y asegúrate de haber elegido origen y destino de la lista de sugerencias, no solo escrito el nombre."),
       ("¿Necesito Internet?",
        "No para buscar. Solo para las incidencias, el retraso oficial de RENFE y, en el seguimiento, la posición del tren. Sin red la aplicación lo indica y sigue funcionando con los horarios."),
       ("¿Por qué el seguimiento no muestra el retraso por GPS?",
        "Necesita permiso de ubicación, señal GPS y haber comprobado que te mueves a velocidad de tren. Mientras tanto muestra «Esperando señal GPS…» o «Comprobando si has embarcado…»."),
       ("He actualizado la aplicación y he perdido los favoritos.",
        "Los favoritos se conservan al actualizar. Solo desaparecen si desinstalas la aplicación o si alguna de sus estaciones ya no existe en los horarios nuevos."),
       ("¿Por qué veo dos tarjetas con el mismo número de tren?",
        "Son variantes del mismo tren con distinta vigencia o recorrido (por ejemplo, el mismo AVE termina en Barcelona unos días y en Figueres otros). Fíjate en la vigencia y el recorrido completo.")]
for q, a in faq:
    story += [KeepTogether([P("<b>%s</b>" % q), P(a)])]

# ---------- 12. Privacidad ----------
story += H1("12. Privacidad")
story += [P("BuscaTrenes no tiene cuentas de usuario, no incluye publicidad y no envía información a ningún servidor propio. Los trayectos favoritos "
            "se guardan únicamente en el dispositivo. La ubicación se usa en el momento en que la pides (estación más cercana, incidencias de tu "
            "zona, seguimiento) y no se almacena. Las únicas conexiones que realiza la aplicación son a los servicios públicos de los operadores "
            "para descargar incidencias y datos en tiempo real."),
          P("Versión %s · %s" % (VERSION, hoy.strftime("%d/%m/%Y")), "cap")]

doc = Doc(OUT)
doc.multiBuild(story)
print("Generado:", OUT, "(%.1f MB)" % (os.path.getsize(OUT) / 1e6))
