"""
CADist_2D - ett slimmat 2D-ritprogram i stil med Microsoft Edge.

Ett enda program med:
  - Ramlost fonster med egen titelrad (minimera / maximera / stang)
  - Menyrad med bara ikoner: Spara, Spara som, Angra, Gor om
  - Knappar for alla entiteter: linje, rektangel, cirkel, bage,
    polylinje, text, plus symboler (block)
  - Ett rutnat i bakgrunden som kan visas/doljas
  - Rutnatets storlek och snappning till rutnatet
  - Spara och oppna DXF

Kor:  pip install PySide6  &&  python ritarprogram.py
"""

import json
import math
import os
import sys

from PySide6.QtCore import Qt, QPointF, QRectF, QSize, QTimer
from PySide6.QtGui import (
    QActionGroup,
    QColor,
    QFont,
    QIcon,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFontComboBox,
    QHBoxLayout,
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

UNIT = 1.0          # en modellenhet = 1 mm i DXF-filen


HELP_TEXT = """Flytta
  Välj Flytta-verktyget (korspilen). Dra en entitet för att
  flytta den, eller dra i tom yta för att flytta hela ritningen.
  Utan verktyg valt fungerar dra direkt på en entitet.
  Piltangenterna flyttar allt (eller markeringen) ett steg,
  Shift + piltangent tio steg. Ctrl+A markerar allt.

Rita
  Välj ett verktyg och klicka i ritytan.
  Linje, rektangel: två klick. Cirkel: centrum + radiepunkt.
  Båge: centrum, start, slut. Text: klick + skriv.
  Polylinje: flera klick, dubbelklick avslutar.
  Symbol: välj i rullgardinen, klicka för att placera.

Färg och bredd
  Två rullgardiner i verktygsraden, båda med en provbild per rad.
  Färg väljer färg, Bredd väljer linjebredd i millimeter. Valet
  gäller nya objekt – har du något markerat ändras det direkt.
  Har du markerat ett objekt visar rullgardinerna dess värden.
  Båda skrivs med i DXF-filen.

Markering och grepppunkter
  Ett markerat objekt visar greppunkter i stället för en ruta:
  kvadrater i ändpunkter och hörn, ring i centrum. Symboler
  visar en ring med kryss i insättningspunkten (Ins.punkt-knappen
  slår av och på dem). Texter har en tunn streckad ram.

Text
  Text-verktyget öppnar en ruta i ritytan. Stäng med Klar,
  Esc eller genom att klicka utanför. Dubbelklick på en text
  ändrar den, och texten flyttas som alla andra objekt.
  Typsnitt och storlek ställs i verktygsraden, och knapparna
  F (fet), K (kursiv), U (understruken), ab (genomstruken),
  x₂ (nedsänkt) och x² (upphöjd) formaterar texten. Har du
  markerat en text slår formateringen igenom direkt.
  Textram-knappen visar eller döljer den tunna ramen.

Rutnät och snapp
  Storleken ställs i rutan bredvid. Knappen Snapp till rutnät
  slår fästningen av och på (även F9). När den är på hamnar
  varje punkt du klickar på exakt på rutnätet; när den är av
  ritar du fritt. Rutnätsknappen visar eller döljer rutnätet.

Nollpunkt och bakgrund
  Nollpunkten i X och Y ritas som ett kors med ring. Origo-knappen
  visar eller döljer den (F7). Centrera sätter den mitt i vyn
  (Ctrl+0), Visa allt zoomar så hela ritningen syns (Ctrl+E).
  Bakgrunden flyttar du med höger- eller mittenknappen, eller
  med piltangenterna när inget är markerat.

Navigering och tangenter
  Rullhjulet zoomar. Höger- eller mittenknapp panorerar.
  Esc avbryter ett verktyg, släpper markeringen och stänger
  textrutan.

Redigera
  Ctrl+A    markera allt
  Ctrl+C    kopiera markerade objekt
  Ctrl+X    klipp ut
  Ctrl+V    klistra in, förskjutet ett steg
  Ctrl+D    dubblera på plats
  Delete    ta bort markerade objekt
  Ctrl+Z    ångra
  Ctrl+Y    gör om

  Backsteg tar bort det senaste objektet.

Block
  Markera några objekt och tryck Ctrl+B, eller använd
  Block-knappen. Objekten blir ett block med ett namn, och
  ersätts av en symbol på samma plats. Blocket hamnar i
  symbolmenyn och kan placeras hur många gånger som helst.
  I DXF-filen skrivs det som BLOCK och varje plats som INSERT.

  Redigera ett eget block: Block-menyn → blockets namn →
  Redigera. Delarna läggs in i ritningen så du kan ändra dem
  med vanliga verktyg. Spara sedan i Block-menyn – alla
  platser på ritningen uppdateras samtidigt.

  Rotera och skala en placerad symbol: markera den och dra
  i den gula ringen för att vrida, eller i någon av de blå
  rutorna för att ändra storlek. Håll Alt för finjustering.
  Vridningen fångar vid jämna 15 grader när snappen är på.

Lager
  Lager-knappen delar upp ritningen i lager. Välj aktivt lager
  överst i menyn – nya objekt hamnar på det lagret. Markera
  objekt och välj Flytta markerade hit för att flytta dem.
  Varje lager kan visas eller döljas, låsas så det inte går att
  markera, ges en egen färg, eller tas bort med sina objekt.
  Lagren skrivs till DXF-filen och läses tillbaka när du öppnar.

Skala
  Skala-knappen har två skalor. Ritningsskalan säger i vilken
  skala ritningen är ritad, till exempel 1:50. Den skrivs med
  i DXF-filen och visas i statusraden. Utskriftsskalan säger
  i vilken skala den skrivs ut. Välj bland de vanliga stegen
  eller ange en egen ritningsskala.

Filer
  Spara DXF – Ctrl+S. Öppna DXF – Ctrl+O.

Xref – bakgrundsritning
  Xref-knappen lägger en annan DXF som blek bakgrund under
  din ritning. Bakgrunden går inte att markera eller flytta
  av misstag, och följer inte med när du sparar. Varje
  bakgrund kan tas bort eller zoomas till för sig.

Sätt in en annan ritning
  Sätt in-knappen lägger en annan DXF i din ritning som
  riktiga objekt du kan redigera. Du anger insättningspunkten
  antingen som X och Y i millimeter, eller genom att peka
  i ritytan."""




# ==========================================================================
# Ikoner - ritas som vektorgrafik, inga bildfiler behovs
# ==========================================================================
# linjebredder i millimeter, i samma steg som CAD-program brukar ha
LINE_WEIGHTS = [0.13, 0.18, 0.25, 0.35, 0.50, 0.70,
                1.00, 1.40, 2.00, 2.50]


def make_color_icon(hex_color, edge="#888", size=18):
    """Fargprov som ikon i rullgardinen."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    r = QRectF(1.5, 1.5, size - 3, size - 3)
    if hex_color:
        p.setBrush(QColor(hex_color))
    else:
        p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(edge), 1.2))
    p.drawEllipse(r)
    p.end()
    return QIcon(pm)


def make_weight_icon(mm, size=22, color="#333"):
    """Liten provbit som visar hur tjock linjen blir."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    # skalan ar fast, sa man ser skillnaden mellan stegen
    px = max(1.0, min(size - 4, mm * 5.0))
    pen = QPen(QColor(color), px)
    pen.setCapStyle(Qt.FlatCap)
    p.setPen(pen)
    y = size / 2
    p.drawLine(QPointF(4, y), QPointF(size - 4, y))
    p.end()
    return QIcon(pm)


def make_icon(draw, size=18, color="#333"):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(Qt.SolidLine)
    pen.setColor(color)
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    draw(p, size)
    p.end()
    return QIcon(pm)


def draw_save(p, s):
    p.drawRoundedRect(2, 2, s - 4, s - 4, 2, 2)
    p.drawRect(s - 8, 3, 5, 5)
    p.drawRect(5, s - 9, s - 10, 7)


def draw_save_as(p, s):
    draw_save(p, s)
    p.drawLine(s - 7, s - 7, s - 2, s - 2)


def draw_open(p, s):
    p.drawPolyline([QPointF(2, s - 4), QPointF(2, 5), QPointF(7, 5),
                    QPointF(9, 8), QPointF(s - 2, 8)])
    p.drawLine(2, s - 4, s - 3, s - 4)


def draw_undo(p, s):
    path = QPainterPath()
    path.moveTo(4, 9)
    path.cubicTo(6, 4, s - 2, 5, s - 3, 9)
    p.drawPath(path)
    p.drawLine(4, 9, 4, 5)
    p.drawLine(4, 9, 8, 9)


def draw_redo(p, s):
    path = QPainterPath()
    path.moveTo(s - 4, 9)
    path.cubicTo(s - 6, 4, 2, 5, 3, 9)
    p.drawPath(path)
    p.drawLine(s - 4, 9, s - 4, 5)
    p.drawLine(s - 4, 9, s - 8, 9)


def draw_grid(p, s):
    for i in range(3, s, 5):
        p.drawLine(i, 3, i, s - 3)
        p.drawLine(3, i, s - 3, i)


def draw_help(p, s):
    path = QPainterPath()
    path.moveTo(6, 6)
    path.cubicTo(6, 2.5, 12, 2.5, 12, 6)
    path.cubicTo(12, 8.5, 9, 8.5, 9, 10.5)
    p.drawPath(path)
    p.drawPoint(9, 14)


def draw_minimize(p, s):
    p.drawLine(4, s // 2, s - 4, s // 2)


def draw_maximize(p, s):
    p.drawRect(4, 4, s - 8, s - 8)


def draw_close(p, s):
    p.drawLine(5, 5, s - 5, s - 5)
    p.drawLine(s - 5, 5, 5, s - 5)


# Verktygsikoner for ritpanelen
def draw_line_icon(p, s):
    p.drawLine(3, s - 3, s - 3, 3)


def draw_rect_icon(p, s):
    p.drawRect(3, 5, s - 6, s - 10)


def draw_circle_icon(p, s):
    p.drawEllipse(QPointF(s / 2, s / 2), s / 2 - 3, s / 2 - 3)


def draw_arc_icon(p, s):
    p.drawArc(QRectF(3, 4, s - 6, s - 6), 0 * 16, 180 * 16)


def draw_poly_icon(p, s):
    p.drawPolyline([QPointF(3, s - 4), QPointF(7, 4),
                    QPointF(s - 3, 8), QPointF(s - 4, s - 4)])


def draw_text_icon(p, s):
    p.drawLine(4, 4, s - 4, 4)
    p.drawLine(s / 2, 4, s / 2, s - 3)


def draw_symbol_icon(p, s):
    p.drawRect(3, 3, s - 6, s - 6)
    p.drawLine(s / 2, 3, s / 2, s - 3)
    p.drawLine(3, s / 2, s - 3, s / 2)


def draw_select_icon(p, s):
    """En pil, markeraverktygets symbol."""
    path = QPainterPath()
    path.moveTo(5, 3)
    path.lineTo(5, 15)
    path.lineTo(8.5, 12)
    path.lineTo(11, 17)
    path.lineTo(13, 16)
    path.lineTo(10.5, 11)
    path.lineTo(14, 10.5)
    path.closeSubpath()
    p.drawPath(path)


def draw_move_icon(p, s):
    p.drawLine(3, s / 2, s - 3, s / 2)
    p.drawLine(s / 2, 3, s / 2, s - 3)
    p.drawLine(3, s / 2, 6, s / 2 - 3)
    p.drawLine(3, s / 2, 6, s / 2 + 3)
    p.drawLine(s - 3, s / 2, s - 6, s / 2 - 3)
    p.drawLine(s - 3, s / 2, s - 6, s / 2 + 3)
    p.drawLine(s / 2, 3, s / 2 - 3, 6)
    p.drawLine(s / 2, 3, s / 2 + 3, 6)
    p.drawLine(s / 2, s - 3, s / 2 - 3, s - 6)
    p.drawLine(s / 2, s - 3, s / 2 + 3, s - 6)


def draw_trash_icon(p, s):
    p.drawRect(5, 5, s - 10, s - 7)
    p.drawLine(3, 5, s - 3, 5)
    p.drawLine(7, 3, s - 7, 3)
    p.drawLine(8, 8, 8, s - 4)
    p.drawLine(s - 8, 8, s - 8, s - 4)


# ==========================================================================
# Tema
# ==========================================================================
THEMES = {
    "dark": {
        "titlebar": "background:#202020; border-bottom:1px solid #333;",
        "title": "font-size:12px; color:#ddd;",
        "menubar": "background:#2b2b2b; border-bottom:1px solid #3a3a3a;",
        "btn": (
            "QPushButton{border:none;padding:5px 8px;border-radius:4px;"
            "font-size:13px;color:#ddd;background:transparent;}"
            "QPushButton:hover{background:#3d3d3d;}"
            "QPushButton:checked{background:#3d3d3d;}"
            "QPushButton:disabled{color:#666;}"
        ),
        "icon": "#ddd",
        "win_hover": "#3d3d3d",
        "menu": (
            "QMenu{background:#2b2b2b;color:#ddd;border:1px solid #3a3a3a;"
            "padding:4px;}"
            "QMenu::item{padding:6px 24px 6px 24px;border-radius:4px;}"
            "QMenu::item:selected{background:#3d3d3d;}"
            "QMenu::item:disabled{color:#888;}"
            "QMenu::separator{height:1px;background:#3a3a3a;margin:4px 8px;}"
        ),
        "canvas": "background:#1b1b1b;",
        "window_bg": "#1e1e1e",
        "window_border": "#3a3a3a",
        "grid": "#2e2e2e",
        "grid_major": "#3a3a3a",
        "axis_x": "#8a4a4a",
        "axis_y": "#4a6a8a",
        "entity": "#e0e0e0",
        "preview": "#6ea8fe",
        "text_frame": "#555555",
        "insert_point": "#7a7a7a",
        "hover": "#9aa7b8",
        "origin": "#d0a020",
        "grip": "#7fb2ff",
        "grip_rotate": "#ffb020",
        "xref": "#4a4a4a",
        "spin": (
            "QSpinBox{background:#2b2b2b;color:#ddd;border:1px solid #3a3a3a;"
            "border-radius:4px;padding:3px 6px;}"
        ),
        "label": "font-size:12px; color:#bbb;",
        "editor": (
            "QTextEdit{border:none;padding:8px;font-size:13px;"
            "background:#1e1e1e;color:#ddd;}"
        ),
    },
    "light": {
        "titlebar": "background:#f3f3f3; border-bottom:1px solid #e0e0e0;",
        "title": "font-size:12px; color:#333;",
        "menubar": "background:#fafafa; border-bottom:1px solid #e0e0e0;",
        "btn": (
            "QPushButton{border:none;padding:5px 8px;border-radius:4px;"
            "font-size:13px;color:#333;background:transparent;}"
            "QPushButton:hover{background:#e5e5e5;}"
            "QPushButton:checked{background:#dcdcdc;}"
            "QPushButton:disabled{color:#bbb;}"
        ),
        "icon": "#333",
        "win_hover": "#e5e5e5",
        "menu": (
            "QMenu{background:#ffffff;color:#222;border:1px solid #e0e0e0;"
            "padding:4px;}"
            "QMenu::item{padding:6px 24px 6px 24px;border-radius:4px;}"
            "QMenu::item:selected{background:#e5e5e5;}"
            "QMenu::item:disabled{color:#999;}"
            "QMenu::separator{height:1px;background:#e0e0e0;margin:4px 8px;}"
        ),
        "canvas": "background:#ffffff;",
        "window_bg": "#ffffff",
        "window_border": "#dcdcdc",
        "grid": "#e8e8e8",
        "grid_major": "#d0d0d0",
        "axis_x": "#d98a8a",
        "axis_y": "#8ab0d9",
        "entity": "#222222",
        "preview": "#3b82f6",
        "text_frame": "#b0b0b0",
        "insert_point": "#9a9a9a",
        "hover": "#8b98a8",
        "origin": "#c08000",
        "grip": "#2563eb",
        "grip_rotate": "#d97706",
        "xref": "#c8c8c8",
        "spin": (
            "QSpinBox{background:#ffffff;color:#222;border:1px solid #dcdcdc;"
            "border-radius:4px;padding:3px 6px;}"
        ),
        "label": "font-size:12px; color:#555;",
        "editor": (
            "QTextEdit{border:none;padding:8px;font-size:13px;"
            "background:#ffffff;color:#222;}"
        ),
    },
}


def system_theme():
    """Laser Windows-registret for att avgora om morkt lage ar pa."""
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if value == 1 else "dark"
    except Exception:
        return "light"


# ==========================================================================
# Installningar
# ==========================================================================
SETTINGS_PATH = os.path.join(
    os.environ.get("APPDATA") or os.path.expanduser("~"),
    "ritprogram.json",
)


def load_settings():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


# ==========================================================================
# Entiteter
# ==========================================================================
def fmt(v):
    """Skriver ett tal utan onodiga nollor."""
    return f"{v:.6f}".rstrip("0").rstrip(".") or "0"


class _AllMover:
    """Flyttar en grupp entiteter som om de vore en enda."""

    def __init__(self, entities):
        self.entities = list(entities)

    def translate(self, dx, dy):
        for ent in self.entities:
            ent.translate(dx, dy)

    def clone(self):
        return _AllMover(self.entities)


class Xref:
    """En annan ritning inlast som bakgrund (xref).

    Den ritas blekt under den egna ritningen, gar inte att markera
    och skrivs inte med nar man sparar."""

    def __init__(self, path, entities):
        self.path = path
        self.entities = entities
        self.offset = QPointF(0, 0)

    @property
    def name(self):
        return os.path.basename(self.path)

    def bounds(self):
        if not self.entities:
            return 0, 0, 0, 0
        xs0 = [e.bounds()[0] for e in self.entities]
        ys0 = [e.bounds()[1] for e in self.entities]
        xs1 = [e.bounds()[2] for e in self.entities]
        ys1 = [e.bounds()[3] for e in self.entities]
        return min(xs0), min(ys0), max(xs1), max(ys1)

    def translate(self, dx, dy):
        self.offset += QPointF(dx, dy)

    def draw(self, p, view, color, width=1.0):
        """Ritar bakgrunden blekt. Fargen blandas mot vit/svart."""
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(color), width))
        for ent in self.entities:
            self._draw_one(p, view, ent)

    def _draw_one(self, p, view, ent):
        off = self.offset
        if isinstance(ent, Line):
            p.drawLine(view.map(ent.a + off), view.map(ent.b + off))
        elif isinstance(ent, Rect):
            pts = [c + off for c in ent._corners()]
            for a, b in zip(pts, pts[1:] + pts[:1]):
                p.drawLine(view.map(a), view.map(b))
        elif isinstance(ent, Circle):
            p.drawEllipse(view.map(ent.c + off),
                          ent.r * view.scale, ent.r * view.scale)
        elif isinstance(ent, Arc):
            path = QPainterPath()
            span = (ent.end - ent.start) % 360 or 360
            first = True
            for k in range(33):
                ang = ent.start + span * k / 32
                pt = QPointF(
                    ent.c.x() + ent.r * math.cos(math.radians(ang)),
                    ent.c.y() + ent.r * math.sin(math.radians(ang))) + off
                sp = view.map(pt)
                if first:
                    path.moveTo(sp); first = False
                else:
                    path.lineTo(sp)
            p.drawPath(path)
        elif isinstance(ent, Polyline):
            pts = [c + off for c in ent.pts]
            if ent.closed and len(pts) > 2:
                pts = pts + [pts[0]]
            for a, b in zip(pts, pts[1:]):
                p.drawLine(view.map(a), view.map(b))
        elif isinstance(ent, Text):
            f = QFont(ent.family)
            f.setPointSizeF(max(6.0, ent.height * view.scale))
            p.setFont(f)
            p.drawText(view.map(ent.pos + off), ent.txt)
        elif isinstance(ent, Insert):
            off2 = ent.pos + off
            for e in ent.definition.entities:
                ghost = Insert(ent.definition, off2, ent.rotation, ent.scale)
                ghost.draw(p, view)


# standardlager, sa en ny ritning har nagot att ligga pa
DEFAULT_LAYER = "0"
LAYER_COLORS = ["#e81123", "#2563eb", "#16a34a", "#d97706",
                "#7c3aed", "#0891b2", "#be185d", "#4b5563"]


class Layer:
    """Ett lager: namn, farg och synlighet."""

    def __init__(self, name, color=None, visible=True, locked=False):
        self.name = name
        self.color = color
        self.visible = visible
        self.locked = locked

    def __repr__(self):
        return f"Layer({self.name})"


class Entity:
    kind = "?"
    # 256 = "ByLayer", alltsa ritningens grundfarg
    color = None

    def clone(self):
        """Kopia av entiteten, sa den kan kopieras och klistras in."""
        raise NotImplementedError
    # linjebredd i mm; None = ritningens grundbredd
    lw = None
    # vilket lager entiteten ligger pa
    layer = DEFAULT_LAYER

    def draw(self, painter, view):
        raise NotImplementedError
    def dxf(self):
        raise NotImplementedError
    def translate(self, dx, dy):
        raise NotImplementedError
    def bounds(self):
        """Returnerar (x0, y0, x1, y1) i modellkoordinater."""
        raise NotImplementedError

    def dxf_color(self):
        """Farg som DXF-kod 62, om entiteten har en egen farg."""
        if not self.color:
            return []
        return [(62, cad_index(self.color))]

    def dxf_width(self):
        """Linjebredd i hundradels mm som DXF-kod 370."""
        if not self.lw:
            return []
        return [(370, int(round(self.lw * 100)))]

    def dxf_layer(self):
        """Lagernamn som DXF-kod 8."""
        return [(8, self.layer or DEFAULT_LAYER)]


def pen_for(ent, theme, view, layer_color=None):
    """Bygger en penna med entitetens farg och linjebredd.

    Har entiteten ingen egen farg anvands lagrets farg, om lagret har
    nagon. Annars temats grundfarg.
    """
    if getattr(ent, "color", None):
        col = ent.color
    elif layer_color:
        col = layer_color
    else:
        col = theme["entity"]
    try:
        width = float(ent.lw) if getattr(ent, "lw", None) else 0.25
    except (TypeError, ValueError):
        width = 0.25
    if not (width > 0):
        width = 0.25
    px = max(1.0, min(40.0, width * view.scale))
    # en tunn linje ar alltid minst 1 px, annars blir den osynlig
    return QPen(QColor(col), px)


def cad_index(hex_color):
    """Narmaste av AutoCAD:s 9 standardfarger for en hex-farg."""
    table = [
        (1, "#ff0000"), (2, "#ffff00"), (3, "#00ff00"),
        (4, "#00ffff"), (5, "#0000ff"), (6, "#ff00ff"),
        (7, "#000000"), (8, "#808080"), (9, "#c0c0c0"),
    ]
    try:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
    except Exception:
        return 7
    best, best_d = 7, 10 ** 9
    for idx, hx in table:
        rr = int(hx[1:3], 16); gg = int(hx[3:5], 16); bb = int(hx[5:7], 16)
        d = (r - rr) ** 2 + (g - gg) ** 2 + (b - bb) ** 2
        if d < best_d:
            best, best_d = idx, d
    return best


DXF_INDEX_COLORS = {
    1: "#ff0000", 2: "#ffff00", 3: "#00ff00", 4: "#00ffff",
    5: "#0000ff", 6: "#ff00ff", 7: "#000000", 8: "#808080",
    9: "#c0c0c0", 256: None,
}

PALETTE = [
    ("Grundfärg (följer temat)", None),
    ("Svart", "#000000"),
    ("Vit", "#ffffff"),
    ("Röd", "#e81123"),
    ("Gul", "#f2c200"),
    ("Grön", "#16a34a"),
    ("Cyan", "#06b6d4"),
    ("Blå", "#2563eb"),
    ("Magenta", "#d946ef"),
    ("Ljusgrå", "#c0c0c0"),
    ("Grå", "#808080"),
    ("Mörkgrå", "#404040"),
]


class Line(Entity):
    kind = "linje"
    def __init__(self, a, b, color=None, lw=None):
        self.a, self.b = a, b
        self.color = color
        self.lw = lw
    def clone(self):
        return Line(QPointF(self.a), QPointF(self.b), self.color, self.lw)
    def draw(self, p, view):
        p.drawLine(view.map(self.a), view.map(self.b))
    def dxf(self):
        return "LINE", ([(10, self.a.x()), (20, self.a.y()),
                         (11, self.b.x()), (21, self.b.y())]
                        + self.dxf_color() + self.dxf_width()
                        + self.dxf_layer())
    def translate(self, dx, dy):
        self.a += QPointF(dx, dy)
        self.b += QPointF(dx, dy)
    def bounds(self):
        return (min(self.a.x(), self.b.x()), min(self.a.y(), self.b.y()),
                max(self.a.x(), self.b.x()), max(self.a.y(), self.b.y()))


class Rect(Entity):
    kind = "rektangel"
    def __init__(self, a, b, color=None, lw=None):
        self.a, self.b = a, b
        self.color = color
        self.lw = lw
    def clone(self):
        return Rect(QPointF(self.a), QPointF(self.b), self.color, self.lw)
    def _corners(self):
        return [self.a,
                QPointF(self.b.x(), self.a.y()),
                self.b,
                QPointF(self.a.x(), self.b.y())]
    def draw(self, p, view):
        p.drawRect(QRectF(view.map(self.a), view.map(self.b)).normalized())
    def dxf(self):
        out = [(90, 4), (70, 1)]
        for c in self._corners():
            out += [(10, c.x()), (20, c.y())]
        return "LWPOLYLINE", (out + self.dxf_color() + self.dxf_width()
                              + self.dxf_layer())
    def translate(self, dx, dy):
        self.a += QPointF(dx, dy)
        self.b += QPointF(dx, dy)
    def bounds(self):
        return (min(self.a.x(), self.b.x()), min(self.a.y(), self.b.y()),
                max(self.a.x(), self.b.x()), max(self.a.y(), self.b.y()))


class Circle(Entity):
    kind = "cirkel"
    def __init__(self, c, r, color=None, lw=None):
        self.c, self.r = c, r
        self.color = color
        self.lw = lw
    def clone(self):
        return Circle(QPointF(self.c), self.r, self.color, self.lw)
    def draw(self, p, view):
        p.drawEllipse(view.map(self.c), self.r * view.scale, self.r * view.scale)
    def dxf(self):
        return "CIRCLE", ([(10, self.c.x()), (20, self.c.y()),
                           (40, self.r)] + self.dxf_color()
                          + self.dxf_width() + self.dxf_layer())
    def translate(self, dx, dy):
        self.c += QPointF(dx, dy)
    def bounds(self):
        return (self.c.x() - self.r, self.c.y() - self.r,
                self.c.x() + self.r, self.c.y() + self.r)


class Arc(Entity):
    kind = "bage"
    def __init__(self, c, r, start, end, color=None, lw=None):
        self.c, self.r, self.start, self.end = c, r, start, end
        self.color = color
        self.lw = lw
    def clone(self):
        return Arc(QPointF(self.c), self.r, self.start, self.end,
                   self.color, self.lw)
    def draw(self, p, view):
        rect = QRectF(view.map(self.c), self.r * view.scale,
                      self.r * view.scale).normalized()
        span = (self.end - self.start) % 360
        if span == 0:
            span = 360
        p.drawArc(rect, int(self.start * 16), int(span * 16))
    def dxf(self):
        return "ARC", ([(10, self.c.x()), (20, self.c.y()), (40, self.r),
                        (50, self.start), (51, self.end)] + self.dxf_color()
                       + self.dxf_width() + self.dxf_layer())
    def translate(self, dx, dy):
        self.c += QPointF(dx, dy)
    def bounds(self):
        pts = [self.c + QPointF(self.r * math.cos(math.radians(self.start)),
                                self.r * math.sin(math.radians(self.start)))]
        span = (self.end - self.start) % 360 or 360
        for k in range(1, 33):
            ang = self.start + span * k / 32
            pts.append(self.c + QPointF(self.r * math.cos(math.radians(ang)),
                                        self.r * math.sin(math.radians(ang))))
        xs = [p.x() for p in pts]
        ys = [p.y() for p in pts]
        return min(xs), min(ys), max(xs), max(ys)


class Polyline(Entity):
    kind = "polylinje"
    def __init__(self, pts, closed=False, color=None, lw=None):
        self.pts = list(pts)
        self.closed = closed
        self.color = color
        self.lw = lw
    def clone(self):
        return Polyline([QPointF(p) for p in self.pts], self.closed,
                        self.color, self.lw)
    def draw(self, p, view):
        pts = self.pts + ([self.pts[0]] if self.closed and len(self.pts) > 2 else [])
        for a, b in zip(pts, pts[1:]):
            p.drawLine(view.map(a), view.map(b))
    def dxf(self):
        out = [(90, len(self.pts)), (70, 1 if self.closed else 0)]
        for pt in self.pts:
            out += [(10, pt.x()), (20, pt.y())]
        return "LWPOLYLINE", (out + self.dxf_color() + self.dxf_width()
                              + self.dxf_layer())
    def translate(self, dx, dy):
        self.pts = [p + QPointF(dx, dy) for p in self.pts]
    def bounds(self):
        xs = [p.x() for p in self.pts]
        ys = [p.y() for p in self.pts]
        return min(xs), min(ys), max(xs), max(ys)


class Text(Entity):
    kind = "text"
    def __init__(self, pos, txt, height=5.0,
                 family="Segoe UI", bold=False, italic=False,
                 underline=False, strikeout=False, sub=False, sup=False,
                 color=None, lw=None):
        self.pos, self.txt, self.height = pos, txt, height
        self.color = color
        self.lw = lw
        self.family, self.bold, self.italic = family, bold, italic
        self.underline, self.strikeout = underline, strikeout
        self.sub, self.sup = sub, sup

    def _font(self, view):
        f = QFont(self.family)
        f.setPointSizeF(max(6.0, self.height * view.scale))
        f.setBold(self.bold)
        f.setItalic(self.italic)
        f.setUnderline(self.underline)
        f.setStrikeOut(self.strikeout)
        return f

    def frame_rect(self, view):
        """Skarmrektangel runt texten, for den tunna ramen."""
        x0, y0, x1, y1 = self.bounds()
        return QRectF(view.map(QPointF(x0, y1)),
                      view.map(QPointF(x1, y0))).normalized()

    def draw(self, p, view):
        p.setFont(self._font(view))
        pos = view.map(self.pos)
        if self.sub or self.sup:
            # lagre eller hogre lage, i linje med formaterad text
            dy = self.height * view.scale * (0.28 if self.sub else -0.30)
            size = self._font(view)
            size.setPointSizeF(max(5.0, size.pointSizeF() * 0.72))
            p.setFont(size)
            pos = QPointF(pos.x(), pos.y() + dy)
        p.drawText(pos, self.txt)

    def dxf(self):
        """DXF:s TEXT-entitet har inget typsnitt i R12, sa bara hojden
        foljer med. Ovrig formatering finns kvar i programmet."""
        h = self.height * (0.72 if (self.sub or self.sup) else 1.0)
        return "TEXT", ([(10, self.pos.x()), (20, self.pos.y()),
                         (40, h), (1, self.txt)] + self.dxf_color()
                        + self.dxf_width() + self.dxf_layer())

    def translate(self, dx, dy):
        self.pos += QPointF(dx, dy)

    def bounds(self):
        w = len(self.txt) * self.height * 0.6
        h = self.height * (0.72 if (self.sub or self.sup) else 1.0)
        return (self.pos.x(), self.pos.y() - h * 0.3,
                self.pos.x() + w, self.pos.y() + h)

    def hit(self, pt, tol):
        x0, y0, x1, y1 = self.bounds()
        return (x0 - tol <= pt.x() <= x1 + tol and
                y0 - tol <= pt.y() <= y1 + tol)

    def clone(self):
        c = Text(QPointF(self.pos), self.txt, self.height,
                 self.family, self.bold, self.italic,
                 self.underline, self.strikeout, self.sub, self.sup,
                 self.color, self.lw)
        return c


# ==========================================================================
# Symboler (block)
# ==========================================================================
class BlockDef:
    """En ateranvandbar symbol. Innehaller entiteter i sina egna
    koordinater, med insattningspunkten i (0, 0)."""

    def __init__(self, name, entities):
        self.name = name
        self.entities = entities

    def instance(self):
        return Insert(self, QPointF(0, 0), 0.0, 1.0)

    def count_instances(self, entities):
        """Hur manga platser pa ritningen som anvander blocket."""
        return sum(1 for e in entities
                   if isinstance(e, Insert) and e.definition is self)

    def bounds(self):
        xs0, ys0, xs1, ys1 = [], [], [], []
        for e in self.entities:
            x0, y0, x1, y1 = e.bounds()
            xs0.append(x0); ys0.append(y0); xs1.append(x1); ys1.append(y1)
        if not xs0:
            return -1, -1, 1, 1
        return min(xs0), min(ys0), max(xs1), max(ys1)


class Insert(Entity):
    """En symbol placerad pa ritningen."""
    kind = "symbol"

    def __init__(self, definition, pos, rotation=0.0, scale=1.0,
                 color=None, lw=None):
        self.definition = definition
        self.pos = pos
        self.rotation = rotation
        self.scale = scale
        self.color = color
        self.lw = lw
        self.ent_layer = None

    # transformerar en punkt fran symbolens koordinater till ritningen
    def _to_model(self, pt):
        a = math.radians(self.rotation)
        x = pt.x() * self.scale
        y = pt.y() * self.scale
        return QPointF(self.pos.x() + x * math.cos(a) - y * math.sin(a),
                       self.pos.y() + x * math.sin(a) + y * math.cos(a))

    def draw(self, p, view):
        # ritar symbolens entiteter direkt, transformerade
        base = p.pen()
        for e in self.definition.entities:
            col = self.color or e.color
            w = (self.lw if self.lw else (e.lw or 0.25)) * view.scale
            if col:
                p.setPen(QPen(QColor(col), max(1.0, w)))
            else:
                p.setPen(QPen(base.color(), max(1.0, w)))
            self._draw_transformed(e, p, view)
        p.setPen(base)

    def _draw_transformed(self, e, p, view):
        if isinstance(e, Line):
            p.drawLine(view.map(self._to_model(e.a)),
                       view.map(self._to_model(e.b)))
        elif isinstance(e, Rect):
            pts = [self._to_model(c) for c in e._corners()]
            for a, b in zip(pts, pts[1:] + pts[:1]):
                p.drawLine(view.map(a), view.map(b))
        elif isinstance(e, Circle):
            p.drawEllipse(view.map(self._to_model(e.c)),
                          e.r * self.scale * view.scale,
                          e.r * self.scale * view.scale)
        elif isinstance(e, Arc):
            path = QPainterPath()
            span = (e.end - e.start) % 360 or 360
            first = True
            for k in range(33):
                ang = e.start + span * k / 32
                pt = e.c + QPointF(e.r * math.cos(math.radians(ang)),
                                   e.r * math.sin(math.radians(ang)))
                sp = view.map(self._to_model(pt))
                if first:
                    path.moveTo(sp); first = False
                else:
                    path.lineTo(sp)
            p.drawPath(path)
        elif isinstance(e, Polyline):
            pts = [self._to_model(c) for c in e.pts]
            if e.closed and len(pts) > 2:
                pts = pts + [pts[0]]
            for a, b in zip(pts, pts[1:]):
                p.drawLine(view.map(a), view.map(b))
        elif isinstance(e, Text):
            f = QFont(e.family)
            f.setBold(e.bold)
            f.setItalic(e.italic)
            f.setUnderline(e.underline)
            f.setStrikeOut(e.strikeout)
            storlek = e.height * self.scale * view.scale
            if not (storlek > 0):
                storlek = 6.0
            f.setPointSizeF(max(6.0, storlek))
            p.setFont(f)
            p.drawText(view.map(self._to_model(e.pos)), e.txt)

    def clone(self):
        return Insert(self.definition, QPointF(self.pos), self.rotation,
                      self.scale, self.color, self.lw)

    def dxf(self):
        return "INSERT", ([(2, self.definition.name),
                           (10, self.pos.x()), (20, self.pos.y()),
                           (41, self.scale), (42, self.scale),
                           (50, self.rotation)] + self.dxf_color()
                          + self.dxf_width() + self.dxf_layer())

    def translate(self, dx, dy):
        self.pos += QPointF(dx, dy)

    def bounds(self):
        x0, y0, x1, y1 = self.definition.bounds()
        pts = [self._to_model(QPointF(x, y))
               for x in (x0, x1) for y in (y0, y1)]
        xs = [p.x() for p in pts]
        ys = [p.y() for p in pts]
        return min(xs), min(ys), max(xs), max(ys)


# --- inbyggda symboler ----------------------------------------------------
def builtin_blocks():
    door = BlockDef("DORR", [
        Line(QPointF(0, 0), QPointF(0, 90)),
        Arc(QPointF(0, 0), 90, 90, 0),
        Line(QPointF(0, 0), QPointF(90, 0)),
    ])
    window = BlockDef("FONSTER", [
        Line(QPointF(0, 0), QPointF(100, 0)),
        Line(QPointF(0, 12), QPointF(100, 12)),
        Line(QPointF(0, 0), QPointF(0, 12)),
        Line(QPointF(100, 0), QPointF(100, 12)),
    ])
    chair = BlockDef("STOL", [
        Rect(QPointF(-15, -15), QPointF(15, 15)),
        Rect(QPointF(-15, 15), QPointF(15, 22)),
        Circle(QPointF(0, 0), 16),
    ])
    valve = BlockDef("VENTIL", [
        Line(QPointF(-20, -14), QPointF(0, 0)),
        Line(QPointF(0, 0), QPointF(-20, 14)),
        Line(QPointF(20, -14), QPointF(0, 0)),
        Line(QPointF(0, 0), QPointF(20, 14)),
    ])
    bolt = BlockDef("BULT", [
        Circle(QPointF(0, 0), 6),
        Polyline([QPointF(-4.2, -4.2), QPointF(-4.2, 4.2),
                  QPointF(4.2, 4.2), QPointF(4.2, -4.2)], closed=True),
    ])
    return [door, window, chair, valve, bolt] + electrical_blocks()


# ==========================================================================
# Elsymboler - svenska standardbeteckningar
# ==========================================================================
# skalsteg som gar att valja
SCALE_CHOICES = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]

# namn pa de inbyggda symbolerna, grupperade i menyn
RIT_SYMBOLS = ["DORR", "FONSTER", "STOL", "VENTIL", "BULT"]
EL_SYMBOLS = ["BRYTARE", "FRANSKILJARE", "VAGLARE", "SLUTARE", "KONTAKT",
              "SPOLE", "RELAE", "MOTOR", "TRANSFORMATOR", "SÄKRING",
              "LAMPA", "KOPPLINGSPUNKT", "JORD", "UTTAG"]

R = 6.0          # kontaktpunktens radie
A = 14.0         # hur langt anslutningsstrecket gar ut


def electrical_blocks():
    """Vanliga elsymboler, ritade enligt svensk standard."""
    ut = []

    def b(namn, delar):
        ut.append(BlockDef(namn, delar))

    # --- brytare och kontakter ----------------------------------------
    b("BRYTARE", [
        Circle(QPointF(-A, 0), R), Circle(QPointF(A, 0), R),
        Line(QPointF(-A + R, 0), QPointF(0, 0)),
        Line(QPointF(0, 0), QPointF(A - R, -R * 1.6)),
        Line(QPointF(A - R, 0), QPointF(A, 0)),
        Circle(QPointF(0, 0), R * 0.5),
    ])
    b("FRANSKILJARE", [
        Circle(QPointF(-A, 0), R), Circle(QPointF(A, 0), R),
        Line(QPointF(-A + R, 0), QPointF(-4, 0)),
        Line(QPointF(-4, 0), QPointF(-4, 9)),
        Line(QPointF(4, -9), QPointF(4, 0)),
        Line(QPointF(4, 0), QPointF(A - R, 0)),
        Circle(QPointF(-4, 11), R * 0.6),
        Circle(QPointF(4, -11), R * 0.6),
    ])
    b("VAGLARE", [
        Circle(QPointF(-A, 0), R), Circle(QPointF(A, 0), R),
        Line(QPointF(-A + R, 0), QPointF(-6, 0)),
        Line(QPointF(-6, 6), QPointF(-6, -6)),
        Line(QPointF(-6, 0), QPointF(0, 0)),
        Line(QPointF(0, 0), QPointF(6, 0)),
        Circle(QPointF(-6, 9), R * 0.6),
        Line(QPointF(6, 0), QPointF(A - R, 0)),
    ])
    b("SLUTARE", [
        Circle(QPointF(-A, 0), R), Circle(QPointF(A, 0), R),
        Line(QPointF(-A + R, 0), QPointF(-5, 0)),
        Line(QPointF(-5, 0), QPointF(5, 0)),
        Line(QPointF(5, 0), QPointF(A - R, 0)),
        Line(QPointF(0, -5), QPointF(0, -12)),
    ])
    b("KONTAKT", [
        Circle(QPointF(-A, 0), R), Circle(QPointF(A, 0), R),
        Line(QPointF(-A + R, 0), QPointF(-6, 0)),
        Line(QPointF(-6, 9), QPointF(8, 0)),
        Line(QPointF(8, 0), QPointF(A - R, 0)),
        Line(QPointF(-6, 9), QPointF(-6, -4)),
        Line(QPointF(4, 4), QPointF(8, 8)),
        Line(QPointF(8, 8), QPointF(4, 8)),
        Line(QPointF(8, 8), QPointF(8, 4)),
    ])

    # --- spolar och motorer -------------------------------------------
    b("SPOLE", [
        Circle(QPointF(-A, 0), R), Circle(QPointF(A, 0), R),
        Polyline([QPointF(-A + R, 0), QPointF(-10, 0), QPointF(-10, 9),
                  QPointF(-3, 9), QPointF(-3, 0), QPointF(3, 0),
                  QPointF(3, 9), QPointF(10, 9), QPointF(10, 0),
                  QPointF(A - R, 0)]),
    ])
    b("RELAE", [
        Rect(QPointF(-A, -9), QPointF(A, 9)),
        Polyline([QPointF(-A + 2, 3), QPointF(-2, 3), QPointF(-2, -3),
                  QPointF(2, -3), QPointF(2, 3), QPointF(A - 2, 3)]),
        Line(QPointF(-A, 0), QPointF(-A, 0)),
    ])
    b("MOTOR", [
        Circle(QPointF(-A, 0), R), Circle(QPointF(A, 0), R),
        Circle(QPointF(0, 0), 14),
        Line(QPointF(-A + R, 0), QPointF(-14, 0)),
        Line(QPointF(14, 0), QPointF(A - R, 0)),
        Line(QPointF(-7, 0), QPointF(-7, 0)),
    ])
    b("TRANSFORMATOR", [
        Circle(QPointF(-A, 0), R), Circle(QPointF(A, 0), R),
        Circle(QPointF(-5, 0), 12), Circle(QPointF(5, 0), 12),
        Line(QPointF(-A + R, 0), QPointF(-17, 0)),
        Line(QPointF(17, 0), QPointF(A - R, 0)),
    ])

    # --- skydd och ljuskallor -----------------------------------------
    b("SÄKRING", [
        Circle(QPointF(-A, 0), R), Circle(QPointF(A, 0), R),
        Rect(QPointF(-9, -5), QPointF(9, 5)),
        Line(QPointF(-A + R, 0), QPointF(-9, 0)),
        Line(QPointF(9, 0), QPointF(A - R, 0)),
        Line(QPointF(-9, 0), QPointF(9, 0)),
    ])
    b("LAMPA", [
        Circle(QPointF(-A, 0), R), Circle(QPointF(A, 0), R),
        Circle(QPointF(0, 0), 11),
        Line(QPointF(-A + R, 0), QPointF(-11, 0)),
        Line(QPointF(11, 0), QPointF(A - R, 0)),
        Line(QPointF(-7.8, -7.8), QPointF(7.8, 7.8)),
        Line(QPointF(-7.8, 7.8), QPointF(7.8, -7.8)),
    ])
    b("KOPPLINGSPUNKT", [
        Circle(QPointF(0, 0), R),
    ])
    b("JORD", [
        Line(QPointF(0, 0), QPointF(0, 10)),
        Line(QPointF(-12, 10), QPointF(12, 10)),
        Line(QPointF(-8, 15), QPointF(8, 15)),
        Line(QPointF(-4, 20), QPointF(4, 20)),
    ])
    b("UTTAG", [
        Arc(QPointF(0, 8), 20, 180, 360),
        Line(QPointF(-20, 8), QPointF(20, 8)),
        Circle(QPointF(-7, 1), 2.5),
        Circle(QPointF(7, 1), 2.5),
        Circle(QPointF(-12, -11), 2.5),
        Circle(QPointF(12, -11), 2.5),
    ])

    return ut


# ==========================================================================
# Ritningsytan - med rutnat och snappning
# ==========================================================================
class GridView:
    """Hjalpare som oversatter mellan modellkoordinater och skarm."""

    def __init__(self, canvas):
        self.canvas = canvas

    @property
    def scale(self):
        return self.canvas.scale

    def map(self, pt):
        c = self.canvas
        return QPointF(c.origin.x() + pt.x() * c.scale,
                       c.origin.y() - pt.y() * c.scale)


class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(380)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.entities = []
        self.blocks = builtin_blocks()
        self.mode = None                  # aktivt verktyg
        self.buttons = {}                 # verktyg -> knapp
        self.pending = []
        self.cursor = None
        self.symbol_to_place = None

        # ritningsskala och utskriftsskala, som 1:50
        self.draw_scale = 50              # ritningen ar ritad i 1:50
        self.print_scale = 1              # skrivs ut 1:1

        self.scale = 2.0                  # px per enhet
        # origo en bit in fran nedre vanstra hornet, sa ritningen far plats
        self.origin_margin = 60           # px
        self.origin = QPointF(80, 400)    # var origo ligger i widgeten
        self.origin_placed = False        # satts nar ritytan fatt sin storlek

        self.grid_on = True
        self.grid_step = 10               # enheter per rutnatsruta
        self.grid_snap = True

        # farg for nya objekt, och ram runt texten
        self.draw_color = None
        self.text_frames = True
        # visa insattningspunkter for symboler
        self.show_insert_points = True
        # linjebredd i mm for nya objekt
        self.line_weight = 0.25

        # aktuell textformatering, vald i verktygsraden
        self.text_family = "Segoe UI"
        self.text_height = 5.0
        self.text_bold = False
        self.text_italic = False
        self.text_underline = False
        self.text_strikeout = False
        self.text_sub = False
        self.text_sup = False
        self.text_color = None

        self.theme = THEMES["light"]
        self.view = GridView(self)

        # markeringsruta
        self._rubber_from = None
        self._rubber_to = None

        # panorering av bakgrunden
        self._pan = None
        self.pan_with_space = False

        # redigering av block
        self.editing_block = None
        self.edit_parts = []

        # lager: namn, farg, synlighet. Alltid minst ett, kallat "0"
        self.layers = [Layer(DEFAULT_LAYER, None, True)]
        self.active_layer = DEFAULT_LAYER

        # osparade andringar
        self.changed = False

        # historik for angra och gor om
        self.HISTORY_MAX = 200
        self.history = []          # andringar som gatt
        self.future = []           # andringar som angrats

        # urklipp for objekt
        self.clipboard = []
        self.paste_count = 0
        self.selection = []               # (entitet, startposition)
        self._drag_entity = None
        self._drag_last = None
        self.hover_ent = None
        self._last_click_pos = None
        self._last_click_ms = 0
        # grepp for vridning och skalning
        self._grip = None
        self._grip_ent = None
        self._grip_ref = None
        self._grip_screen = None

        # nollpunkten och bakgrunden
        self.show_origin = True
        self.origin_size = 12          # px, hur stor nollpunktsmarkeringen ar
        self.pan_speed = 1.0

        # bakgrundsritningar (xref)
        self.xrefs = []
        self.xref_visible = True

    # --- koordinater ---
    def to_model(self, pos):
        return QPointF(
            (pos.x() - self.origin.x()) / self.scale,
            -(pos.y() - self.origin.y()) / self.scale,
        )

    def snap(self, pt):
        if not (self.grid_on and self.grid_snap):
            return pt
        g = float(self.grid_step)
        return QPointF(round(pt.x() / g) * g, round(pt.y() / g) * g)

    # --- tema ---
    def apply_theme(self, theme):
        self.theme = theme
        self.setStyleSheet(theme["canvas"])
        self.update()

    # --- verktyg ---
    def set_tool(self, tool):
        """Valknapparna ar checkbara, sa ett andra klick stanger av."""
        for name, btn in self.buttons.items():
            btn.setChecked(name == tool and self.mode != tool)
        self.mode = None if self.mode == tool else tool
        self.pending = []
        if self.mode != "symbol":
            self.symbol_to_place = None
        if self.mode != "sattin":
            cb = getattr(self, "on_cancel_insert", None)
            if cb is not None:
                cb()
        if self.mode != "blockpunkt":
            cb = getattr(self, "on_cancel_block_origin", None)
            if cb is not None:
                cb()
        self.update()
        self.setFocus()

    def clear_tool(self):
        self.mode = None
        self.pending = []
        self.symbol_to_place = None
        cb = getattr(self, "on_cancel_insert", None)
        if cb is not None:
            cb()
        cb = getattr(self, "on_cancel_block_origin", None)
        if cb is not None:
            cb()
        for btn in self.buttons.values():
            btn.setChecked(False)
        self.update()

    # --- interaktion ---
    def mousePressEvent(self, e):
        # ett klick utanfor textrutan stanger den och sparar.
        # forsta klicket efter att rutan oppnats hoppas over, annars
        # stangs den av samma klick som oppnade den.
        if getattr(self, "text_editor", None) is not None:
            if getattr(self, "_editor_open_guard", False):
                self._editor_open_guard = False
            else:
                self.finish_text_editor()

        # kom ihag klicket, sa dubbelklicket kan oppna texten
        self._last_click_pos = QPointF(e.position())
        self._last_click_ms = e.timestamp() if hasattr(e, "timestamp") else 0

        pt = self.snap(self.to_model(e.position()))

        # mittenknapp eller hogerknapp = panorera bakgrunden
        if e.button() == Qt.MiddleButton or e.button() == Qt.RightButton:
            self._pan = e.position()
            # behall musen under hela draget, sa rorelsen nar fram
            self.grabMouse()
            self.setCursor(Qt.ClosedHandCursor)
            return

        if e.button() != Qt.LeftButton:
            return

        if self.mode == "markera":
            self._marker_click(e, pt)
            return

        if self.mode is None or self.mode == "skjut":
            hit = self._hit_test(self.to_model(e.position()))
            if hit and hit not in self.selection:
                self.selection = [hit]
            elif hit is None:
                self.selection = []
            self.sync_toolbar()
            # ett klick pa ett markerat objekt startar en flytt av
            # hela markeringen; annars bara det man klickade pa
            if hit is not None and hit in self.selection and len(self.selection) > 1:
                self._drag_entity = _AllMover(self.selection)
            else:
                self._drag_entity = hit if hit else (
                    _AllMover(self.entities) if self.mode == "skjut" else None)
            self._drag_last = self.to_model(e.position())
            self.update()
            return

        if self.mode is None:
            self._start_move(self.to_model(e.position()))
            return

        if self.mode in ("linje", "rektangel"):
            self.pending.append(pt)
            if len(self.pending) == 2:
                self._commit(Line if self.mode == "linje" else Rect,
                             self.pending[0], self.pending[1])
                self.pending = []

        elif self.mode == "cirkel":
            self.pending.append(pt)
            if len(self.pending) == 2:
                r = math.hypot(self.pending[1].x() - self.pending[0].x(),
                               self.pending[1].y() - self.pending[0].y())
                if r > 0:
                    self._commit(Circle, self.pending[0], r)
                self.pending = []

        elif self.mode == "bage":
            self.pending.append(pt)
            if len(self.pending) == 3:
                c = self.pending[0]
                a1 = math.degrees(math.atan2(self.pending[1].y() - c.y(),
                                             self.pending[1].x() - c.x()))
                a2 = math.degrees(math.atan2(self.pending[2].y() - c.y(),
                                             self.pending[2].x() - c.x()))
                r = math.hypot(self.pending[1].x() - c.x(),
                               self.pending[1].y() - c.y())
                if r > 0:
                    self._commit(Arc, c, r, a1, a2)
                self.pending = []

        elif self.mode == "polylinje":
            self.pending.append(pt)

        elif self.mode == "text":
            hit = self._hit_test_text(self.to_model(e.position()))
            if hit is not None:
                self._edit_text(hit)
            else:
                self._open_text_editor(None, pt)

        elif self.mode == "symbol" and self.symbol_to_place:
            self._commit(Insert, self.symbol_to_place, pt)

        elif self.mode == "sattin":
            cb = getattr(self, "on_place_insert", None)
            if cb is not None and cb(pt):
                self.clear_tool()

        elif self.mode == "blockpunkt":
            cb = getattr(self, "on_place_block_origin", None)
            if cb is not None and cb(pt):
                self.clear_tool()

        self.update()

    def mouseMoveEvent(self, e):
        if self._pan is not None:
            delta = e.position() - self._pan
            self.origin += delta
            self._pan = e.position()
            self.update()
            return

        self.cursor = self.snap(self.to_model(e.position()))

        # markeringsrutan ritas medan man drar
        if self.mode == "markera" and self._rubber_from is not None:
            self._marker_drag(e)
            return

        # ett grepp haller pa att dras
        if self._grip is not None:
            fine = bool(e.modifiers() & Qt.AltModifier)
            self._grip_screen = QPointF(e.position())
            self._apply_grip(self.to_model(e.position()), fine=fine)
            return

        # vilken entitet star muspekaren over?
        if self.mode in (None, "skjut"):
            new_hover = self._hit_test(self.to_model(e.position()))
            if new_hover is not self.hover_ent:
                self.hover_ent = new_hover
                self.setCursor(Qt.PointingHandCursor if new_hover
                               else Qt.ArrowCursor)
                self.update()

        if self._drag_entity is not None:
            cur = self.to_model(e.position())
            dx = cur.x() - self._drag_last.x()
            dy = cur.y() - self._drag_last.y()
            self._drag_last = cur
            self._drag_entity.translate(dx, dy)
            self.update()
            return

        if self.pending:
            self.update()

    def mouseReleaseEvent(self, e):
        if self.mode == "markera" and self._rubber_from is not None:
            self._marker_release()
            return
        if self._grip is not None:
            self.releaseMouse()
            self._grip = None
            self._grip_ent = None
            self._grip_ref = None
            self.sync_toolbar()
            self.update()
        if self._pan is not None:
            self.releaseMouse()
            self.setCursor(Qt.ArrowCursor)
            self._pan = None
        self._drag_entity = None

    def leaveEvent(self, e):
        """Slapper musen om pekaren lamnar ritytan under ett drag."""
        if self._pan is not None:
            self.releaseMouse()
            self.setCursor(Qt.ArrowCursor)
            self._pan = None
        super().leaveEvent(e)

    def mouseDoubleClickEvent(self, e):
        if self.mode == "polylinje" and len(self.pending) >= 2:
            self._commit(Polyline, self.pending)
            self.pending = []
            self.update()
            return

        # dubbelklick pa en text ger redigering, oavsett verktyg.
        # prova bade den aktuella positionen och det senaste klicket,
        # sa traffen inte gar forlorad mellan press och dblclick.
        if getattr(self, "text_editor", None) is not None:
            return
        for pos in (e.position(),
                    getattr(self, "_last_click_pos", None)):
            if pos is None:
                continue
            hit = self._hit_test_text(self.to_model(pos))
            if hit is not None:
                self._edit_text(hit)
                return

    # --- textinmatning ---
    def _hit_test_text(self, model_pt):
        """Hittar en text nara punkten, sa den kan redigeras."""
        # lite rundare tolerans an for flytt, sa texten ar latt att traffa
        tol = 8 / self.scale
        for ent in reversed(self.entities):
            if isinstance(ent, Text) and ent.hit(model_pt, tol):
                return ent
        return None

    def _open_text_editor(self, existing, model_pt):
        """Oppnar en flytande ruta i ritytan for att skriva eller andra text."""
        # stang en ruta som redan star oppen, sa bara en finns i taget
        if getattr(self, "text_editor", None) is not None:
            self._close_text_editor(True)
        self._editor_existing = existing
        self._editor_pos = QPointF(model_pt)

        box = QTextEdit(self)
        box.setAcceptRichText(False)
        box.setPlaceholderText("Skriv text …")
        box.setTabChangesFocus(False)
        box.setFixedSize(300, 92)
        box.setWindowModality(Qt.NonModal)
        box.setAttribute(Qt.WA_DeleteOnClose, False)

        if existing is not None:
            box.setPlainText(existing.txt)
            h = existing.height
            fam = existing.family
            sty = (existing.bold, existing.italic, existing.underline,
                   existing.strikeout, existing.sub, existing.sup)
            col = existing.color
        else:
            h = self.text_height
            fam = self.text_family
            sty = (self.text_bold, self.text_italic, self.text_underline,
                   self.text_strikeout, self.text_sub, self.text_sup)
            col = self.text_color
        self._editor_style = (h, fam, sty, col, self.line_weight)

        # lagg rutan nara platsen, men innanfor ritytan
        sp = self.view.map(model_pt)
        x = int(min(max(sp.x() + 12, 0), max(0, self.width() - 280)))
        y = int(min(max(sp.y() - 20, 0), max(0, self.height() - 110)))
        box.move(x, y)
        box.setStyleSheet(
            "QTextEdit{background:#ffffff;color:#111;border:1px solid "
            "#3b82f6;border-radius:4px;padding:4px;font-size:13px;}")
        box.textChanged.connect(self._grow_text_editor)
        box.installEventFilter(self)
        box.show()
        box.raise_()
        # satt state fore fokus, annars tappar Qt fokus igen
        self.text_editor = box
        self._editor_open_guard = True

        ok = getattr(self, "text_ok_btn", None)
        if ok is not None:
            ok.move(x + 300 - 96, y + 92 + 2)
            ok.raise_()
            ok.show()

        box.activateWindow()
        box.setFocus(Qt.OtherFocusReason)

    def _grow_text_editor(self):
        """Lat rutan vaxa med innehallet."""
        box = getattr(self, "text_editor", None)
        if box is None:
            return
        doc_h = int(box.document().size().height()) + 20
        box.setFixedHeight(max(84, min(220, doc_h)))
        ok = getattr(self, "text_ok_btn", None)
        if ok is not None:
            ok.move(box.x() + box.width() - ok.width(),
                    box.y() + box.height() + 2)
            ok.raise_()

    def _close_text_editor(self, commit):
        box = getattr(self, "text_editor", None)
        if box is None:
            return
        # las av ALLT innan rutan tas bort
        txt = box.toPlainText()
        pos = QPointF(getattr(self, "_editor_pos", QPointF(0, 0)))
        existing = getattr(self, "_editor_existing", None)
        style = getattr(self, "_editor_style", None)
        if style is None:
            h, fam = self.text_height, self.text_family
            sty, col, lw = (False,) * 6, self.text_color, self.line_weight
        else:
            h, fam, sty, col, lw = style

        # rensa state forst, sa aterkommande signaler inte kraschar
        self.text_editor = None
        self._editor_existing = None
        ok = getattr(self, "text_ok_btn", None)
        if ok is not None:
            ok.hide()
        box.blockSignals(True)
        box.hide()
        box.deleteLater()

        text = txt.strip()
        if text:
            if existing is not None and existing in self.entities:
                # andra den befintliga texten pa plats
                existing.txt = text
                existing.height = h
                existing.family = fam
                (existing.bold, existing.italic, existing.underline,
                 existing.strikeout, existing.sub, existing.sup) = sty
                existing.color = col
                existing.lw = lw
                self.selection = [existing]
            else:
                text_ent = Text(pos, text, h, family=fam,
                                bold=sty[0], italic=sty[1],
                                underline=sty[2], strikeout=sty[3],
                                sub=sty[4], sup=sty[5], color=col, lw=lw)
                self.entities.append(text_ent)
                self.selection = [text_ent]
                self.mark(("add", text_ent))
        self.update()
        self.setFocus()
        self.sync_toolbar()

    def eventFilter(self, obj, event):
        """Esc i textrutan stanger den och sparar."""
        if (getattr(self, "text_editor", None) is obj
                and event.type() == event.Type.KeyPress
                and event.key() == Qt.Key_Escape):
            self._close_text_editor(True)
            return True
        return super().eventFilter(obj, event)

    def finish_text_editor(self):
        """Anropas nar rutan tappar fokus: spara det som skrivits."""
        if getattr(self, "text_editor", None) is not None:
            self._close_text_editor(True)

    def focusOutEvent(self, e):
        # lat rutan leva vidare; stangningen sker via knappen eller Esc
        super().focusOutEvent(e)

    def _edit_text(self, ent):
        self._open_text_editor(ent, QPointF(ent.pos))
        if hasattr(self, "text_editor") and self.text_editor is not None:
            self.text_editor.selectAll()

    def keyPressEvent(self, e):
        # Esc stanger textrutan forst, sa den inte lamnar ritytan
        if getattr(self, "text_editor", None) is not None:
            if e.key() == Qt.Key_Escape:
                self._close_text_editor(True)
            return
        self._handle_key(e)

    def close_text_editor_if_any(self):
        self.finish_text_editor()

    def _keypress_normal(self, e):
        old = self.scale
        factor = 1.15 if e.angleDelta().y() > 0 else 1 / 1.15
        self.scale = max(0.05, min(50.0, old * factor))
        # hall punkten under musen stilla
        m = e.position()
        model = QPointF((m.x() - self.origin.x()) / old,
                        -(m.y() - self.origin.y()) / old)
        self.origin = QPointF(m.x() - model.x() * self.scale,
                              m.y() + model.y() * self.scale)
        self.update()

    def _handle_key(self, e):
        ctrl = e.modifiers() & Qt.ControlModifier
        step = 10 if e.modifiers() & Qt.ShiftModifier else 1

        if ctrl and e.key() == Qt.Key_C:
            if self.copy_selection():
                e.accept()
            return
        if ctrl and e.key() == Qt.Key_X:
            if self.cut_selection():
                e.accept()
            return
        if ctrl and e.key() == Qt.Key_V:
            if self.paste_clipboard():
                e.accept()
            return
        if ctrl and e.key() == Qt.Key_D:
            if self.duplicate_selection():
                e.accept()
            return
        if ctrl and e.key() == Qt.Key_A:
            self.select_all()
            e.accept()
            return
        if ctrl and e.key() == Qt.Key_Y:
            self.redo()
        elif e.key() == Qt.Key_Escape:
            if self._rubber_from is not None:
                self._rubber_from = None
                self._rubber_to = None
                self.update()
                return
            if self._grip is not None:
                self.releaseMouse()
                self._grip = None
                self._grip_ent = None
                self.setCursor(Qt.ArrowCursor)
                return
            if self._pan is not None:
                self.releaseMouse()
                self.setCursor(Qt.ArrowCursor)
                self._pan = None
                return
            self.clear_tool()
            if self.selection:
                self.selection = []
                self.hover_ent = None
                self.sync_toolbar()
            self.update()
        elif e.key() == Qt.Key_Backspace:
            self.undo()
        elif e.key() == Qt.Key_Delete:
            self.delete_selection()
        elif e.key() in (Qt.Key_Left, Qt.Key_Right,
                         Qt.Key_Up, Qt.Key_Down):
            dx = -1 if e.key() == Qt.Key_Left else (1 if e.key() == Qt.Key_Right else 0)
            dy = -1 if e.key() == Qt.Key_Down else (1 if e.key() == Qt.Key_Up else 0)
            if not self.nudge(dx * step, dy * step):
                e.ignore()

    def delete_selection(self):
        if not self.selection:
            return
        bort = [e for e in self.selection if e in self.entities]
        for ent in bort:
            self.entities.remove(ent)
        self.mark([("del", e) for e in bort])
        self.selection = []
        self.sync_toolbar()
        self.update()

    # --- klipp och klistra in ---
    def copy_selection(self):
        """Kopierar markerade objekt till urklippet."""
        if not self.selection:
            return False
        self.clipboard = [e.clone() for e in self.selection]
        self.paste_count = 0
        self.sync_toolbar()
        self.update()
        return True

    def cut_selection(self):
        """Klipper ut markerade objekt: kopierar och tar bort dem."""
        if not self.selection:
            return False
        self.clipboard = [e.clone() for e in self.selection]
        self.paste_count = 0
        bort = [e for e in self.selection if e in self.entities]
        for ent in bort:
            self.entities.remove(ent)
        self.mark([("del", e) for e in bort])
        self.selection = []
        self.sync_toolbar()
        self.update()
        return True

    def paste_clipboard(self):
        """Klistrar in urklippet, lite forskjutet for varje gang."""
        if not self.clipboard:
            return False
        self.paste_count += 1
        # varje inklistring forskjuts sa kopiorna inte ligger ovanpa
        shift = self.grid_step * self.paste_count
        new = []
        for ent in self.clipboard:
            c = ent.clone()
            c.translate(shift, -shift)
            if getattr(c, "color", None) is None:
                c.color = self.draw_color
            new.append(c)
        self.entities.extend(new)
        self.selection = new
        self.mark([("add", e) for e in new])
        self.sync_toolbar()
        self.update()
        return True

    def duplicate_selection(self):
        """Dubblerar markerade objekt pa plats, med ett stegs forskjutning."""
        if not self.selection:
            return False
        new = []
        for ent in self.selection:
            c = ent.clone()
            c.translate(self.grid_step, -self.grid_step)
            new.append(c)
        self.entities.extend(new)
        self.selection = new
        self.mark([("add", e) for e in new])
        self.update()
        return True

    # --- block ---
    def block_name_taken(self, name):
        return any(b.name.upper() == name.upper() for b in self.blocks)

    # --- lager ---
    def layer(self, name):
        """Hittar ett lager med namnet, eller None."""
        for lag in self.layers:
            if lag.name == name:
                return lag
        return None

    def layer_visible(self, name):
        lag = self.layer(name)
        return lag.visible if lag else True

    def layer_locked(self, name):
        lag = self.layer(name)
        return lag.locked if lag else False

    def visible_entities(self):
        """Bara de entiteter vars lager ar synligt."""
        return [e for e in self.entities if self.layer_visible(e.layer)]

    def add_layer(self, name, color=None):
        """Skapar ett nytt lager om namnet ar ledigt."""
        name = (name or "").strip()
        if not name or self.layer(name) is not None:
            return None
        if color is None:
            n = len(self.layers)
            color = LAYER_COLORS[(n - 1) % len(LAYER_COLORS)]
        lag = Layer(name, color, True)
        self.layers.append(lag)
        return lag

    def remove_layer(self, name):
        """Tar bort ett lager och allt som ligger pa det."""
        if name == DEFAULT_LAYER:
            return False
        lag = self.layer(name)
        if lag is None:
            return False
        bort = [e for e in self.entities if e.layer == name]
        for e in bort:
            self.entities.remove(e)
        self.mark([("del", e) for e in bort])
        self.layers.remove(lag)
        if self.active_layer == name:
            self.active_layer = DEFAULT_LAYER
        self.selection = []
        self.update()
        return True

    def move_selection_to_layer(self, name):
        """Flyttar markerade objekt till ett lager."""
        if self.layer(name) is None:
            return False
        n = 0
        for e in self.selection:
            e.layer = name
            n += 1
        self.update()
        return n

    def set_layer_visible(self, name, visible):
        lag = self.layer(name)
        if lag is not None:
            lag.visible = visible
            self.selection = [e for e in self.selection
                              if self.layer_visible(e.layer)]
            self.update()

    def set_layer_locked(self, name, locked):
        lag = self.layer(name)
        if lag is not None:
            lag.locked = locked
            self.update()

    def set_layer_color(self, name, color):
        lag = self.layer(name)
        if lag is not None:
            lag.color = color
            self.update()

    # --- redigera ett befintligt block ---
    def start_block_edit(self, blk):
        """Oppnar ett block for redigering.

        Blockets delar laggs in i ritningen som vanliga objekt pa ett
        eget lager, medan placeringarna star kvar. Nar man ar klar
        skrivs andringen tillbaka och alla placeringar följer med.
        """
        if self.editing_block is not None:
            return None
        self.editing_block = blk
        # arbetslagret: kopior av blockets delar, i samma koordinater
        self.edit_parts = [e.clone() for e in blk.entities]
        self.entities.extend(self.edit_parts)
        self.selection = list(self.edit_parts)
        self.sync_toolbar()
        self.update()
        return blk

    def finish_block_edit(self, keep=True):
        """Avslutar redigeringen och skriver tillbaka till blocket."""
        blk = self.editing_block
        if blk is None:
            return None
        parts = list(getattr(self, "edit_parts", []))
        self.editing_block = None
        self.edit_parts = []
        self.selection = []

        # ta bort arbetslagret ur ritningen
        for e in parts:
            if e in self.entities:
                self.entities.remove(e)

        if keep and parts:
            # skriv tillbaka: delarna blir blockets nya innehall
            blk.entities = parts
        self.sync_toolbar()
        self.update()
        return blk

    def cancel_block_edit(self):
        return self.finish_block_edit(keep=False)

    def remove_block(self, blk):
        """Tar bort blocket ur listan och alla dess platser pa ritningen."""
        self.entities = [
            e for e in self.entities
            if not (isinstance(e, Insert) and e.definition is blk)
        ]
        if blk in self.blocks:
            self.blocks.remove(blk)
        self.selection = []
        self.update()
        return blk

    def explode_insert(self, ins, keep_definition=False):
        """Loser upp en placerad symbol till vanliga objekt.

        Delarna laggs in pa ritningen pa samma plats, med symbolens
        rotation och skalning inraknad. Symbolen tas bort.
        """
        if not isinstance(ins, Insert):
            return None
        x0, y0, x1, y1 = ins.bounds()
        delar = []
        for e in ins.definition.entities:
            c = self._transform_clone(e, ins)
            delar.append(c)

        if ins not in self.entities:
            return None
        self.entities.remove(ins)
        self.entities.extend(delar)

        if not keep_definition:
            self._drop_definition_if_unused(ins.definition)

        self.selection = delar
        self.mark([("del", ins)] + [("add", d) for d in delar])
        self.sync_toolbar()
        self.update()
        return delar

    def _transform_clone(self, e, ins):
        """Kopia av en del, flyttad till ritningen med rotation och skala."""
        c = e.clone()
        # om det redan ar en placerad symbol: rakna om den forst
        if isinstance(c, Insert):
            c.rotation += ins.rotation
            c.scale *= ins.scale
            c.pos = ins._to_model(c.pos)
            return c

        # for enkel geometri: bygg om punkterna via symbolens transform
        if isinstance(c, Line):
            c.a, c.b = ins._to_model(c.a), ins._to_model(c.b)
        elif isinstance(c, Rect):
            c.a, c.b = ins._to_model(c.a), ins._to_model(c.b)
        elif isinstance(c, Circle):
            c.c = ins._to_model(c.c)
            c.r = c.r * ins.scale
        elif isinstance(c, Arc):
            # centrum flyttas, radien skalas, vinkeln vrids
            c.c = ins._to_model(c.c)
            c.r = c.r * ins.scale
            c.start = (c.start + ins.rotation) % 360
            c.end = (c.end + ins.rotation) % 360
        elif isinstance(c, Polyline):
            c.pts = [ins._to_model(pt) for pt in c.pts]
        elif isinstance(c, Text):
            c.pos = ins._to_model(c.pos)
            c.height = c.height * ins.scale

        if c.color is None:
            c.color = ins.color
        if c.lw is None:
            c.lw = ins.lw
        return c

    def _drop_definition_if_unused(self, blk):
        """Tar bort blockets definition om ingen plats anvander den."""
        if blk.count_instances(self.entities) == 0:
            if blk in self.blocks:
                self.blocks.remove(blk)

    def drop_unused_definitions(self):
        """Stadar bort blockdefinitioner som inte langre anvands."""
        borta = [b for b in self.blocks
                 if b.count_instances(self.entities) == 0
                 and b not in builtin_blocks()]
        for b in borta:
            self.blocks.remove(b)
        return borta

    def next_block_name(self):
        """Foreslar ett ledigt namn."""
        n = 1
        while self.block_name_taken(f"BLOCK{n}"):
            n += 1
        return f"BLOCK{n}"

    def create_block(self, name, origin=None):
        """Gor ett nytt block av markerade entiteter.

        Entiteterna flyttas till blockets egna koordinater med
        insattningspunkten i origo, och ersatts av en symbol pa plats.
        """
        if len(self.selection) < 1:
            return None
        name = (name or "").strip().upper()
        if not name:
            return None
        if self.block_name_taken(name):
            return None

        picked = list(self.selection)

        # insattningspunkten: vald punkt, annars nedre vanstra hornet
        # av de markerade delarna
        if origin is None:
            ox = min(e.bounds()[0] for e in picked)
            oy = min(e.bounds()[1] for e in picked)
            origin = QPointF(ox, oy)
        else:
            origin = QPointF(origin.x(), origin.y())

        # kopior till blockdefinitionen, forskjutna sa att
        # insattningspunkten hamnar i blockets origo (0, 0)
        parts = []
        for ent in picked:
            c = ent.clone()
            c.translate(-origin.x(), -origin.y())
            parts.append(c)

        blk = BlockDef(name, parts)
        self.blocks.append(blk)

        # ta bort originalen och lagg symbolen pa platsen
        for ent in picked:
            if ent in self.entities:
                self.entities.remove(ent)

        ins = Insert(blk, QPointF(origin))
        if self.draw_color:
            ins.color = None
        self.entities.append(ins)
        self.selection = [ins]
        self.mark([("del", e) for e in picked] + [("add", ins)])
        self.sync_toolbar()
        self.update()
        return blk

    def set_selection_color(self, color):
        """Satter farg pa markerade objekt. Utan markering: nya objekt."""
        self.draw_color = color
        for ent in self.selection:
            ent.color = color
        self.update()

    def set_selection_weight(self, mm):
        """Satter linjebredd pa markerade objekt. Utan markering: nya objekt."""
        self.line_weight = mm
        for ent in self.selection:
            ent.lw = mm
        self.update()

    # --- markera-verktyget ---
    def _marker_click(self, e, pt):
        """Ett klick i markera-laget: valj eller valj bort ett objekt."""
        hit = self._hit_test(self.to_model(e.position()))
        if hit is None:
            # tom yta: borja rita en markeringsruta
            self._rubber_from = QPointF(self.to_model(e.position()))
            self._rubber_to = QPointF(self._rubber_from)
            if not (e.modifiers() & Qt.ShiftModifier):
                self.selection = []
                self.sync_toolbar()
            self.update()
            return

        if e.modifiers() & Qt.ShiftModifier:
            # skift: vaxla objektet i markeringen
            if hit in self.selection:
                self.selection.remove(hit)
            else:
                self.selection.append(hit)
        else:
            self.selection = [hit]
        self.sync_toolbar()
        self.update()

    def _marker_drag(self, e):
        """Uppdaterar markeringsrutan medan man drar."""
        self._rubber_to = QPointF(self.to_model(e.position()))
        self.update()

    def _marker_release(self):
        """Avslutar rutan och markerar allt innanfor."""
        if self._rubber_from is None:
            return
        x0 = min(self._rubber_from.x(), self._rubber_to.x())
        y0 = min(self._rubber_from.y(), self._rubber_to.y())
        x1 = max(self._rubber_from.x(), self._rubber_to.x())
        y1 = max(self._rubber_from.y(), self._rubber_to.y())
        vikt = abs(x1 - x0) * abs(y1 - y0)

        if vikt > (4 / self.scale) ** 2:
            # rutan ar stor nog: markera allt som ligger innanfor
            for ent in self.entities:
                if not self.layer_visible(ent.layer):
                    continue
                if self.layer_locked(ent.layer):
                    continue
                ex0, ey0, ex1, ey1 = ent.bounds()
                if ex0 >= x0 and ey0 >= y0 and ex1 <= x1 and ey1 <= y1:
                    if ent not in self.selection:
                        self.selection.append(ent)
        self._rubber_from = None
        self._rubber_to = None
        self.sync_toolbar()
        self.update()

    def select_in_box(self, x0, y0, x1, y1, shift=False):
        """Markerar allt inom en ruta. Anvands aven fran menyn."""
        if not shift:
            self.selection = []
        for ent in self.entities:
            if not self.layer_visible(ent.layer):
                continue
            if self.layer_locked(ent.layer):
                continue
            ex0, ey0, ex1, ey1 = ent.bounds()
            if ex0 >= x0 and ey0 >= y0 and ex1 <= x1 and ey1 <= y1:
                if ent not in self.selection:
                    self.selection.append(ent)
        self.sync_toolbar()
        self.update()
        return len(self.selection)

    def select_all(self):
        """Markerar allt som gar att markera."""
        self.selection = [
            e for e in self.entities
            if self.layer_visible(e.layer) and not self.layer_locked(e.layer)
        ]
        self.sync_toolbar()
        self.update()
        return len(self.selection)

    def _start_move(self, model_pt):
        """Klicka pa en entitet nar inget verktyg ar valt = flytta den."""
        hit = self._hit_test(model_pt)
        self.selection = [hit] if hit else []
        self._drag_entity = hit
        self._drag_last = model_pt
        self.sync_toolbar()

    def _hit_test(self, model_pt):
        """Hittar den oversta entiteten nara punkten, annars None.

        Ett block ar en enhet: ett klick var som helst inom dess ruta
        tar hela blocket, sa det gar att gripa och flytta pa ett stalle.
        Delarna andrar man genom att losa upp blocket.
        """
        tol = 6 / self.scale
        for ent in reversed(self.entities):
            if not self.layer_visible(ent.layer):
                continue
            if self.layer_locked(ent.layer):
                continue
            x0, y0, x1, y1 = ent.bounds()
            if (x0 - tol <= model_pt.x() <= x1 + tol and
                    y0 - tol <= model_pt.y() <= y1 + tol):
                return ent
        return None

    def nudge(self, dx, dy):
        """Flyttar allt, eller bara markeringen om nagot ar markerat."""
        targets = self.selection or self.entities
        if not targets:
            return False
        for ent in targets:
            ent.translate(dx * self.grid_step, dy * self.grid_step)
        self.update()
        return True

    def move_all_by(self, dx, dy):
        """Flyttar hela ritningen ett antal enheter."""
        if not self.entities:
            return False
        for ent in self.entities:
            ent.translate(dx, dy)
        self.update()
        return True

    def move_selection_to(self, x, y):
        """Flyttar markerade entiteter sa att deras nedre vanstra hornnar (x, y)."""
        targets = self.selection
        if not targets:
            return False
        xs0 = min(e.bounds()[0] for e in targets)
        ys0 = min(e.bounds()[1] for e in targets)
        dx, dy = x - xs0, y - ys0
        for ent in targets:
            ent.translate(dx, dy)
        self.update()
        return True

    def sync_toolbar(self):
        """Meddelar fonstret att verktygsraden ska uppdateras."""
        cb = getattr(self, "on_selection_change", None)
        if cb is not None:
            cb()

    def _commit(self, cls, *args):
        ent = cls(*args)
        if getattr(ent, "color", None) is None:
            ent.color = self.draw_color
        if getattr(ent, "lw", None) is None:
            ent.lw = self.line_weight
        ent.layer = self.active_layer
        self.entities.append(ent)
        self.selection = [ent]
        self.mark(("add", ent))
        self.update()

    # --- redigering ---
    def mark(self, payload):
        """Lagger en andring pa historiken, sa den kan angras.

        payload: lista av ("add", entitet) eller ("del", entitet).
        """
        if isinstance(payload, tuple):
            payload = [payload]
        if not payload:
            return
        self.changed = True
        self.history.append(list(payload))
        self.future = []
        if len(self.history) > self.HISTORY_MAX:
            self.history.pop(0)

    def _apply(self, payload, backwards=False):
        """Utfor en andring, eller backar den."""
        for atgard, ent in (reversed(payload) if backwards else payload):
            if atgard == "add":
                if backwards:
                    if ent in self.entities:
                        self.entities.remove(ent)
                else:
                    if ent not in self.entities:
                        self.entities.append(ent)
            elif atgard == "del":
                if backwards:
                    if ent not in self.entities:
                        self.entities.append(ent)
                else:
                    if ent in self.entities:
                        self.entities.remove(ent)

    def undo(self):
        if self.pending:
            self.pending = []
            self.update()
            return True
        if not self.history:
            return False
        payload = self.history.pop()
        self._apply(payload, backwards=True)
        self.future.append(payload)
        self.selection = []
        self.sync_toolbar()
        self.update()
        return True

    def redo(self):
        """Spolar framat: gor om det senaste man angrade."""
        if not self.future:
            return False
        payload = self.future.pop()
        self._apply(payload)
        self.history.append(payload)
        self.selection = []
        self.sync_toolbar()
        self.update()
        return True

    def can_undo(self):
        return bool(self.history)

    def can_redo(self):
        return bool(self.future)

    def clear_all(self):
        if not self.entities:
            return
        if QMessageBox.question(
            self, "Rensa", "Ta bort alla entiteter pa ritningen?"
        ) == QMessageBox.Yes:
            self.entities = []
            self.pending = []
            self.update()

    # --- rita ---
    def paintEvent(self, e):
        t = self.theme
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        if self.grid_on:
            self._draw_grid(p, t)

        # xref-bakgrunder, bleka, under den egna ritningen
        if self.xref_visible:
            for xr in self.xrefs:
                xr.draw(p, self.view, t["xref"], 1.0)

        p.setBrush(Qt.NoBrush)
        for ent in self.entities:
            lag = self.layer(ent.layer)
            if lag is not None and not lag.visible:
                continue
            lag_farg = lag.color if lag else None
            p.setPen(pen_for(ent, t, self.view, lag_farg))
            ent.draw(p, self.view)
            # tunn ram runt texten, sa den gar att gripa och flytta
            if isinstance(ent, Text) and self.text_frames:
                p.setPen(QPen(QColor(t["text_frame"]), 1.0, Qt.DashLine))
                p.drawRect(ent.frame_rect(self.view))

        # markering: greppunkter i stallet for rutor runt objekten
        if self.selection:
            for ent in self.selection:
                self._draw_handles(p, ent, t)

        # insattningspunkten for symboler, alltid synlig
        if self.show_insert_points:
            for ent in self.entities:
                if isinstance(ent, Insert) and ent not in self.selection:
                    self._draw_insert_mark(p, ent, t)

        # greppunkter pa den entitet muspekaren star over
        if self.hover_ent is not None and self.hover_ent not in self.selection:
            p.setPen(QPen(QColor(t["hover"]), 1.2))
            self._draw_handles(p, self.hover_ent, t, thin=True)

        # markeringsrutan
        if self._rubber_from is not None and self._rubber_to is not None:
            r = QRectF(self.view.map(self._rubber_from),
                       self.view.map(self._rubber_to)).normalized()
            fyll = QColor(t["preview"])
            fyll.setAlpha(40)
            p.setBrush(fyll)
            p.setPen(QPen(QColor(t["preview"]), 1.0, Qt.DashLine))
            p.drawRect(r)
            p.setBrush(Qt.NoBrush)

        # forhandsvisning
        if self.pending and self.cursor:
            p.setPen(QPen(QColor(t["preview"]), 1.2, Qt.DashLine))
            pts = self.pending + [self.cursor]
            for a, b in zip(pts, pts[1:]):
                p.drawLine(self.view.map(a), self.view.map(b))

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(t["preview"]))
        for pt in self.pending:
            p.drawEllipse(self.view.map(pt), 3, 3)

    # --- grepppunkter ---
    def _pt(self, p, t, model_pt, filled=True, size=3.5):
        """Liten kvadrat i en modellpunkt."""
        sp = self.view.map(model_pt)
        col = QColor(t["preview"])
        if filled:
            p.setPen(Qt.NoPen)
            p.setBrush(col)
        else:
            p.setPen(QPen(col, 1.4))
            p.setBrush(QColor(t["window_bg"]))
        p.drawRect(QRectF(sp.x() - size, sp.y() - size, size * 2, size * 2))
        p.setBrush(Qt.NoBrush)

    def _circle_pt(self, p, t, model_pt, r=4.0, filled=False):
        sp = self.view.map(model_pt)
        col = QColor(t["preview"])
        if filled:
            p.setPen(Qt.NoPen)
            p.setBrush(col)
        else:
            p.setPen(QPen(col, 1.4))
            p.setBrush(QColor(t["window_bg"]))
        p.drawEllipse(sp, r, r)

    def _draw_handles(self, p, ent, t, thin=False):
        """Visa andpunkter, horn och centrum for markerade objekt."""
        p.setBrush(Qt.NoBrush)
        if isinstance(ent, Line):
            self._pt(p, t, ent.a)
            self._pt(p, t, ent.b)
            self._circle_pt(p, t, (ent.a + ent.b) / 2, 3.0)

        elif isinstance(ent, Rect):
            for c in ent._corners():
                self._pt(p, t, c)

        elif isinstance(ent, Circle):
            self._circle_pt(p, t, ent.c, 4.5)
            self._pt(p, t, QPointF(ent.c.x() + ent.r, ent.c.y()))
            self._pt(p, t, QPointF(ent.c.x(), ent.c.y() + ent.r))

        elif isinstance(ent, Arc):
            self._circle_pt(p, t, ent.c, 4.5)
            for ang in (ent.start, ent.end):
                self._pt(p, t, QPointF(
                    ent.c.x() + ent.r * math.cos(math.radians(ang)),
                    ent.c.y() + ent.r * math.sin(math.radians(ang))))

        elif isinstance(ent, Polyline):
            for pt in ent.pts:
                self._pt(p, t, pt)

        elif isinstance(ent, Text):
            # tunn streckad ram + ett grepp i insattningspunkten
            p.setPen(QPen(QColor(t["text_frame"]), 1.0, Qt.DashLine))
            p.setBrush(Qt.NoBrush)
            p.drawRect(ent.frame_rect(self.view))
            self._pt(p, t, ent.pos)

        elif isinstance(ent, Insert):
            self._draw_insert_mark(p, ent, t, strong=True)

    def _draw_insert_mark(self, p, ent, t, strong=False):
        """Ring och kryss dar symbolen sitter."""
        sp = self.view.map(ent.pos)
        col = QColor(t["preview"] if strong else t["insert_point"])
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(col, 1.6))
        r = 7
        p.drawEllipse(sp, r, r)
        p.drawLine(QPointF(sp.x() - r - 3, sp.y()), QPointF(sp.x() + r + 3, sp.y()))
        p.drawLine(QPointF(sp.x(), sp.y() - r - 3), QPointF(sp.x(), sp.y() + r + 3))
        # insattningspunkten ar blockets enda handtag

    def insert_grip_points(self, ent):
        """De fyra grepppunkterna runt en placerad symbol, i modellkoordinater.

        Returnerar en lista av (namn, punkt).
        """
        x0, y0, x1, y1 = ent.bounds()
        cx, cy = ent.pos.x(), ent.pos.y()
        # vridhandtaget sitter en bit ovanfor symbolens hogerhorn
        top = max(y1, cy)
        right = max(x1, cx)
        span = max(20.0, (x1 - x0) * 0.6)
        return [
            ("rotate", QPointF(right + span * 0.5, top + span * 0.5)),
            ("scale", QPointF(right + span * 0.5, y0 - span * 0.5)),
            ("scale_x", QPointF(x0 - span * 0.4, cy)),
            ("scale_y", QPointF(cx, y1 + span * 0.4)),
        ]

    def _draw_insert_grips(self, p, ent, t):
        """Ritar vrid- och skalningsgreppen."""
        col = QColor(t["grip"])
        rot_col = QColor(t["grip_rotate"])
        for namn, pt in self.insert_grip_points(ent):
            sp = self.view.map(pt)
            if namn == "rotate":
                p.setPen(QPen(rot_col, 1.6))
                p.setBrush(QColor(t["window_bg"]))
                p.drawEllipse(sp, 6, 6)
                # en liten pil runt ringen, sa vridningen syns
                p.drawArc(QRectF(sp.x() - 9, sp.y() - 9, 18, 18),
                          40 * 16, 250 * 16)
            else:
                p.setPen(QPen(col, 1.4))
                p.setBrush(QColor(t["window_bg"]))
                p.drawRect(QRectF(sp.x() - 5, sp.y() - 5, 10, 10))
        # en linje ut till vridhandtaget
        x0, y0, x1, y1 = ent.bounds()
        base = QPointF(max(x1, ent.pos.x()), max(y1, ent.pos.y()))
        pts = dict(self.insert_grip_points(ent))
        p.setPen(QPen(rot_col, 1.0, Qt.DashLine))
        p.drawLine(self.view.map(base), self.view.map(pts["rotate"]))

    # --- grepp for vridning och skalning ---
    def _grip_at(self, screen_pos):
        """Finns ett grepp nara muspekaren? Returnerar (namn, entitet)."""
        tol = 9
        for ent in self.selection:
            if not isinstance(ent, Insert):
                continue
            for namn, pt in self.insert_grip_points(ent):
                sp = self.view.map(pt)
                if (abs(sp.x() - screen_pos.x()) <= tol
                        and abs(sp.y() - screen_pos.y()) <= tol):
                    return namn, ent
        return None

    def _start_grip_drag(self, grip, screen_pos=None):
        namn, ent = grip
        self._grip = namn
        self._grip_ent = ent
        # utgangslaget: greppets punkt, inte symbolens insattningspunkt
        pts = dict(self.insert_grip_points(ent))
        self._grip_ref = QPointF(pts.get(namn, ent.pos))

    def _apply_grip(self, model_pt, fine=False):
        """Raknar ut ny vridning eller skalning fran musens lage."""
        if self._grip is None or self._grip_ent is None:
            return
        ent = self._grip_ent
        cx, cy = ent.pos.x(), ent.pos.y()
        dx = model_pt.x() - cx
        dy = model_pt.y() - cy
        r = math.hypot(dx, dy)

        if self._grip == "rotate":
            # vinkeln fran insattningspunkten till musen
            ang = math.degrees(math.atan2(dy, dx))
            if not fine:
                # fanga vid jämna steg om snappen är på
                steg = 15 if self.grid_snap else 1
                ang = round(ang / steg) * steg
            ent.rotation = ang % 360

        else:
            # skalning: hur langt musen ar fran insattningspunkten
            # jamfort med nar draget borjade
            ref = self._grip_ref if self._grip_ref is not None else ent.pos
            r0 = math.hypot(ref.x() - cx, ref.y() - cy)
            if r0 < 1e-6:
                x0, y0, x1, y1 = ent.definition.bounds()
                r0 = max(1.0, max(abs(x1), abs(y1)) * ent.scale)
            faktor = r / r0
            ny = ent.scale * faktor
            if not fine:
                # jamna steg: 0,1 upp till 1, sedan 0,5 och 1
                if ny < 1:
                    ny = round(ny * 10) / 10
                elif ny < 5:
                    ny = round(ny * 2) / 2
                else:
                    ny = float(round(ny))
            ent.scale = max(0.05, min(50.0, ny))
        self.update()

    def _draw_grid(self, p, t):
        step_px = self.grid_step * self.scale
        if step_px < 4:
            return
        w, h = self.width(), self.height()
        # var ligger modellens nollinjer pa skarmen
        ox, oy = self.origin.x(), self.origin.y()

        first_x = ox - math.floor(ox / step_px) * step_px
        x = first_x
        i = 0
        while x <= w:
            col = t["grid_major"] if (i + int(round((x - first_x) / step_px))) % 5 == 0 else t["grid"]
            p.setPen(QPen(QColor(col), 1))
            p.drawLine(QPointF(x, 0), QPointF(x, h))
            x += step_px
            i += 1

        first_y = oy - math.floor(oy / step_px) * step_px
        y = first_y
        j = 0
        while y <= h:
            col = t["grid_major"] if j % 5 == 0 else t["grid"]
            p.setPen(QPen(QColor(col), 1))
            p.drawLine(QPointF(0, y), QPointF(w, y))
            y += step_px
            j += 1

        p.setPen(QPen(QColor(t["axis_x"]), 1.4))
        p.drawLine(QPointF(0, oy), QPointF(w, oy))
        p.setPen(QPen(QColor(t["axis_y"]), 1.4))
        p.drawLine(QPointF(ox, 0), QPointF(ox, h))

        # nollpunkten: ring med kors och en pil utat langs varje axel
        if self.show_origin:
            self._draw_origin(p, t)

    def _draw_origin(self, p, t):
        """Nollpunkten: ring, kors och pilar langs X och Y."""
        o = self.view.map(QPointF(0, 0))
        s0 = self.origin_size
        col = QColor(t["origin"])
        p.setBrush(Qt.NoBrush)

        # ringen
        p.setPen(QPen(col, 2.0))
        p.drawEllipse(o, s0, s0)

        # korset genom ringen
        p.drawLine(QPointF(o.x() - s0 - 7, o.y()),
                   QPointF(o.x() + s0 + 7, o.y()))
        p.drawLine(QPointF(o.x(), o.y() - s0 - 7),
                   QPointF(o.x(), o.y() + s0 + 7))

        # pilar utat langs axlarna, sa riktningen syns
        p.setPen(QPen(col, 1.8))
        for dx, dy in ((1, 0), (0, -1)):
            ax = o.x() + dx * (s0 + 7)
            ay = o.y() + dy * (s0 + 7)
            p.drawLine(QPointF(ax, ay),
                       QPointF(ax + dx * 11, ay + dy * 11))
            # pilsprötet
            p.drawLine(QPointF(ax + dx * 11, ay + dy * 11),
                       QPointF(ax + dx * 11 - dy * 4 - dx * 5,
                               ay + dy * 11 + dx * 4 - dy * 5))
            p.drawLine(QPointF(ax + dx * 11, ay + dy * 11),
                       QPointF(ax + dx * 11 + dy * 4 - dx * 5,
                               ay + dy * 11 - dx * 4 - dy * 5))

        # bokstaverna X och Y vid pilarna
        f = QFont()
        f.setPointSizeF(9.0)
        p.setFont(f)
        p.setPen(QPen(col, 1.0))
        p.drawText(QPointF(o.x() + s0 + 30, o.y() + 13), "X")
        p.drawText(QPointF(o.x() + 7, o.y() - s0 - 24), "Y")

        # sjalva punkten
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawEllipse(o, 2.5, 2.5)

    def resizeEvent(self, e):
        if not self.origin_placed:
            self.origin_home()
            self.origin_placed = True
        super().resizeEvent(e)

    # --- xref ---
    def add_xref(self, path, entities):
        self.xrefs.append(Xref(path, entities))
        self.update()

    def clear_xrefs(self):
        self.xrefs = []
        self.update()

    def remove_xref(self, xref):
        if xref in self.xrefs:
            self.xrefs.remove(xref)
            self.update()

    def origin_home(self):
        """Lagger nollpunkten i nedre vanstra hornet med en liten marginal."""
        m = self.origin_margin
        self.origin = QPointF(m, self.height() - m)
        self.origin_placed = True
        self.update()

    def center_on_origin(self):
        """Panorerar sa nollpunkten hamnar mitt i ritytan."""
        self.origin = QPointF(self.width() / 2, self.height() / 2)
        self.update()

    def zoom_to_fit(self):
        """Zoomar och panorerar sa hela ritningen syns."""
        if not self.entities:
            self.center_on_origin()
            return
        x0 = min(e.bounds()[0] for e in self.entities)
        y0 = min(e.bounds()[1] for e in self.entities)
        x1 = max(e.bounds()[2] for e in self.entities)
        y1 = max(e.bounds()[3] for e in self.entities)
        w = max(1e-6, x1 - x0)
        h = max(1e-6, y1 - y0)
        pad = 40
        self.scale = max(0.05, min(50.0,
                                   min((self.width() - 2 * pad) / w,
                                       (self.height() - 2 * pad) / h)))
        # lagg ritningens mitt i ritytans mitt
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        self.origin = QPointF(self.width() / 2 - cx * self.scale,
                              self.height() / 2 + cy * self.scale)
        self.update()

    # --- DXF ---
    def to_dxf(self):
        # bara den egna ritningen sparas; xref-bakgrunder foljer inte med
        used_inserts = [e for e in self.entities if isinstance(e, Insert)]
        blocks_in_use = []
        for ins in used_inserts:
            if ins.definition not in blocks_in_use:
                blocks_in_use.append(ins.definition)

        # skalans namn i DXF, t.ex. 1:50
        skala_namn = (f"1:{self.draw_scale}" if self.draw_scale > 1
                      else f"{self.draw_scale}:1")
        out = ["0", "SECTION", "2", "HEADER",
               "9", "$ACADVER", "1", "AC1009",
               "9", "$INSUNITS", "70", "4",
               "9", "$MEASUREMENT", "70", "1",
               # ritningsskalan, som AutoCAD och andra kan lasa
               "9", "$DIMSCALE", "40", fmt(self.draw_scale),
               "9", "$LTSCALE", "40", fmt(self.draw_scale),
               "9", "$USERR1", "40", fmt(self.draw_scale),
               "9", "$USERR2", "40", fmt(self.print_scale),
               "9", "$USERS1", "1", skala_namn,
               "0", "ENDSEC"]

        if blocks_in_use:
            out += ["0", "SECTION", "2", "BLOCKS"]
            for blk in blocks_in_use:
                x0, y0, x1, y1 = blk.bounds()
                out += ["0", "BLOCK", "8", "0",
                        "2", blk.name,
                        "70", "0",
                        "10", fmt(x0), "20", fmt(y0), "30", "0",
                        "3", blk.name, "1", ""]
                for e in blk.entities:
                    name, pairs = e.dxf()
                    out += ["0", name]
                    for code, value in pairs:
                        out += [str(code),
                                value if isinstance(value, str) else fmt(value)]
                out += ["0", "ENDBLK", "8", "0"]
            out += ["0", "ENDSEC"]

        # lagertabellen, sa lagerindelningen foljer med i filen
        out += ["0", "SECTION", "2", "TABLES",
                "0", "TABLE", "2", "LAYER", "70", str(len(self.layers))]
        for lag in self.layers:
            out += ["0", "LAYER", "2", lag.name, "70", "0",
                    "62", str(cad_index(lag.color) if lag.color else 7),
                    "6", "CONTINUOUS"]
        out += ["0", "ENDTAB", "0", "ENDSEC"]

        out += ["0", "SECTION", "2", "ENTITIES"]
        for ent in self.entities:
            name, pairs = ent.dxf()
            out += ["0", name]
            for code, value in pairs:
                out += [str(code),
                        value if isinstance(value, str) else fmt(value)]
        out += ["0", "ENDSEC", "0", "EOF"]
        return "\n".join(out) + "\n"


# ==========================================================================
# Huvudfonstret
# ==========================================================================
class FloatingToolbar(QWidget):
    """En flytande verktygspanel som kan dras dit man vill."""

    HANDTAG_H = 18          # hur hog draglisten ar

    def __init__(self, parent):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Verktyg")
        self.setMouseTracking(True)
        self._drag_from = None
        self._hover = False
        self.bar_color = "#fafafa"
        self.border_color = "#dcdcdc"
        self.handle_color = "#b0b0b0"

    def enterEvent(self, e):
        self._hover = True
        if self._drag_from is None:
            self.setCursor(Qt.OpenHandCursor)
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.position().y() <= self.HANDTAG_H:
            self._drag_from = (e.globalPosition().toPoint()
                               - self.frameGeometry().topLeft())
            self.setCursor(Qt.ClosedHandCursor)
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag_from is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_from)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag_from = None
        if self._hover:
            self.setCursor(Qt.OpenHandCursor)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, 10, 10)
        p.fillPath(path, QColor(self.bar_color))
        p.setPen(QPen(QColor(self.border_color), 1))
        p.drawPath(path)

        # draglisten: tre punkter mitt pa panelens overkant
        col = QColor(self.handle_color)
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        cx = self.width() / 2
        cy = self.HANDTAG_H / 2
        for i in (-1, 0, 1):
            p.drawEllipse(QPointF(cx + i * 7, cy), 1.8, 1.8)


class EdgeHandle(QWidget):
    """Tunn list langs en fonsterkant som tar emot musen."""

    def __init__(self, parent, zone):
        super().__init__(parent)
        self.zone = zone
        self.setMouseTracking(True)
        self.setCursor(EdgeHandle.CURSORS.get(zone, Qt.ArrowCursor))
        self.setStyleSheet("background:transparent;border:none;")
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    CURSORS = {
        "left": Qt.SizeHorCursor, "right": Qt.SizeHorCursor,
        "top": Qt.SizeVerCursor, "bottom": Qt.SizeVerCursor,
        "topleft": Qt.SizeFDiagCursor, "bottomright": Qt.SizeFDiagCursor,
        "topright": Qt.SizeBDiagCursor, "bottomleft": Qt.SizeBDiagCursor,
    }

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.grabMouse()
            self.parent()._start_resize(
                self.zone, e.globalPosition().toPoint())
            e.accept()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self.parent()._apply_resize(e.globalPosition().toPoint())
            e.accept()

    def mouseReleaseEvent(self, e):
        self.releaseMouse()
        self.parent()._resize_zone = None
        e.accept()


class DrawingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        # genomskinlig bakgrund sa hornen kan rundas
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1000, 700)
        self.setMinimumSize(520, 380)
        self._drag_pos = None
        self._resize_zone = None
        self._resize_start_geo = None
        self._resize_start_mouse = None
        self._pending_insert = None
        self.path = None

        s = load_settings()
        self.theme_mode = s.get("theme", "system")

        self.corner_radius = 12
        # marginalen ger plats at rundningen OCH at kanthandtagen
        self.edge_margin = 14

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        m = self.edge_margin
        root.setContentsMargins(m, m, m, m)
        root.setSpacing(0)

        # --- titelrad ---
        self.titlebar = QWidget()
        self.titlebar.setFixedHeight(32)
        tb = QHBoxLayout(self.titlebar)
        tb.setContentsMargins(10, 0, 0, 0)
        tb.setSpacing(0)
        self.title = QLabel("CADist 2D Beta – utan namn")
        tb.addWidget(self.title)
        tb.addStretch()

        self.win_buttons = []
        for name, drawer, slot, is_close in [
            ("Minimera", draw_minimize, self.showMinimized, False),
            ("Maximera", draw_maximize, self._toggle_max, False),
            ("Stäng", draw_close, self.close, True),
        ]:
            b = QPushButton()
            b.setFlat(True)
            b.setFixedSize(46, 32)
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(name)
            b.clicked.connect(slot)
            tb.addWidget(b)
            self.win_buttons.append((b, drawer, is_close))

        # --- menyrad ---
        self.menubar = QWidget()
        self.menubar.setFixedHeight(36)
        mb = QHBoxLayout(self.menubar)
        mb.setContentsMargins(8, 0, 8, 0)
        mb.setSpacing(2)

        self.icon_buttons = []
        for drawer, fn, tip in [
            (draw_open, self.open_dxf, "Öppna ritning (Ctrl+O)"),
            (draw_save, self.save_dxf, "Spara DXF (Ctrl+S)"),
            (draw_save_as, self.save_as_dxf, "Spara som DXF (Ctrl+Shift+S)"),
            (draw_undo, self.undo, "Ångra (Ctrl+Z)"),
            (draw_redo, self.redo, "Gör om (Ctrl+Y)"),
        ]:
            btn = QPushButton()
            btn.setFlat(True)
            btn.setFixedWidth(38)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tip)
            btn.clicked.connect(fn)
            mb.addWidget(btn)
            self.icon_buttons.append((btn, drawer))
            if tip.startswith("Ångra"):
                self.undo_btn = btn
            elif tip.startswith("Gör om"):
                self.redo_btn = btn

        self.xref_btn = QPushButton("Xref")
        self.xref_btn.setFlat(True)
        self.xref_btn.setCursor(Qt.PointingHandCursor)
        self.xref_btn.setToolTip("Lägg en annan ritning som blek bakgrund")
        mb.addWidget(self.xref_btn)

        self.layer_btn = QPushButton("Lager")
        self.layer_btn.setFlat(True)
        self.layer_btn.setCursor(Qt.PointingHandCursor)
        self.layer_btn.setToolTip("Lager och lagerindelning")
        mb.addWidget(self.layer_btn)

        # rullgardin for att tanda och slacka lager
        self.layer_box = QComboBox()
        self.layer_box.setFixedWidth(170)
        self.layer_box.setToolTip(
            "Välj lager: ett klick på en rad gör lagret aktivt.\n"
            "Klicka på bocken längst till vänster för att tända eller släcka.")
        # ett val byter aktivt lager
        self.layer_box.activated.connect(self._layer_box_selected)
        # ett klick pa bocken vaxlar synligheten
        self.layer_box.view().pressed.connect(self._layer_box_toggle_click)
        mb.addWidget(self.layer_box)

        self.scale_btn = QPushButton("Skala")
        self.scale_btn.setFlat(True)
        self.scale_btn.setCursor(Qt.PointingHandCursor)
        self.scale_btn.setToolTip("Ritningsskala och utskriftsskala")
        mb.addWidget(self.scale_btn)

        self.block_btn = QPushButton("Block")
        self.block_btn.setFlat(True)
        self.block_btn.setCursor(Qt.PointingHandCursor)
        self.block_btn.setToolTip(
            "Skapa ett block av markerade objekt (Ctrl+B)")
        mb.addWidget(self.block_btn)

        self.insert_btn = QPushButton("Sätt in")
        self.insert_btn.setFlat(True)
        self.insert_btn.setCursor(Qt.PointingHandCursor)
        self.insert_btn.setToolTip("Sätt in en annan ritning i den här")
        mb.addWidget(self.insert_btn)

        self.help_btn = QPushButton("Hjälp")
        self.help_btn.setFlat(True)
        self.help_btn.setCursor(Qt.PointingHandCursor)
        self.help_btn.setToolTip("Hjälp och inställningar")
        mb.addWidget(self.help_btn)
        mb.addStretch()

        # --- flytande verktygspanel: bara ritverktygen ---
        self.canvas = Canvas()

        self.toolbar = FloatingToolbar(self)
        tl = QHBoxLayout(self.toolbar)
        tl.setContentsMargins(8, self.toolbar.HANDTAG_H + 4, 8, 8)
        tl.setSpacing(2)

        tools = [
            ("markera", draw_select_icon,
             "Markera – klicka för att välja, skift för flera,"
             " dra en ruta för att ta allt inom den"),
            ("skjut", draw_move_icon,
             "Flytta – dra det som är markerat, eller hela ritningen"),
            ("linje", draw_line_icon, "Linje"),
            ("rektangel", draw_rect_icon, "Rektangel"),
            ("cirkel", draw_circle_icon, "Cirkel"),
            ("bage", draw_arc_icon, "Båge"),
            ("polylinje", draw_poly_icon, "Polylinje (dubbelklick avslutar)"),
            ("text", draw_text_icon, "Text"),
        ]
        for key, drawer, tip in tools:
            btn = QPushButton()
            btn.setFlat(True)
            btn.setCheckable(True)
            btn.setFixedWidth(36)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(tip)
            btn.clicked.connect(lambda _, k=key: self.canvas.set_tool(k))
            tl.addWidget(btn)
            self.canvas.buttons[key] = btn

        tl.addSpacing(10)

        # symbolknapp med rullgardin
        self.symbol_btn = QPushButton()
        self.symbol_btn.setFlat(True)
        self.symbol_btn.setCheckable(True)
        self.symbol_btn.setFixedWidth(36)
        self.symbol_btn.setCursor(Qt.PointingHandCursor)
        self.symbol_btn.setToolTip("Symboler")
        tl.addWidget(self.symbol_btn)
        self.canvas.buttons["symbol"] = self.symbol_btn
        self._build_symbol_menu()

        # --- fast rad ovanfor ritytan: allt ovrigt ---
        self.toolbar2 = QWidget()
        t2 = QHBoxLayout(self.toolbar2)
        t2.setContentsMargins(8, 2, 8, 2)
        t2.setSpacing(2)

        grid_lbl = QLabel("Rutnät")
        self.grid_label = grid_lbl
        t2.addWidget(grid_lbl)

        self.grid_step_box = QSpinBox()
        self.grid_step_box.setRange(1, 500)
        self.grid_step_box.setValue(self.canvas.grid_step)
        self.grid_step_box.setSuffix(" enheter")
        self.grid_step_box.setFixedWidth(105)
        self.grid_step_box.setToolTip("Rutnätets storlek")
        self.grid_step_box.valueChanged.connect(self._set_grid_step)
        t2.addWidget(self.grid_step_box)

        self.snap_btn = QPushButton("Snapp")
        self.snap_btn.setFlat(True)
        self.snap_btn.setCheckable(True)
        self.snap_btn.setChecked(self.canvas.grid_snap)
        self.snap_btn.setToolTip("Fäst punkter till rutnätet (F9)")
        self.snap_btn.setCursor(Qt.PointingHandCursor)
        self.snap_btn.toggled.connect(self._set_snap)
        t2.addWidget(self.snap_btn)

        self.grid_btn = QPushButton()
        self.grid_btn.setFlat(True)
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.setFixedWidth(32)
        self.grid_btn.setCursor(Qt.PointingHandCursor)
        self.grid_btn.setToolTip("Visa/dölj rutnät")
        self.grid_btn.toggled.connect(self._set_grid_on)
        t2.addWidget(self.grid_btn)

        clear_btn = QPushButton()
        clear_btn.setFlat(True)
        clear_btn.setFixedWidth(32)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setToolTip("Rensa ritningen")
        clear_btn.clicked.connect(self.canvas.clear_all)
        t2.addWidget(clear_btn)

        t2.addSpacing(10)
        self.color_label = QLabel("Färg")
        t2.addWidget(self.color_label)

        self.color_box = QComboBox()
        self.color_box.setFixedWidth(130)
        self.color_box.setToolTip(
            "Färg. Gäller nya objekt – och markerade objekt om du har "
            "något markerat.")
        for label, hexv in PALETTE:
            self.color_box.addItem(make_color_icon(hexv, self._icon_color),
                                   label, hexv)
        self.color_box.setCurrentIndex(0)
        self.color_box.currentIndexChanged.connect(self._pick_color_index)
        t2.addWidget(self.color_box)

        self.weight_label = QLabel("Bredd")
        t2.addWidget(self.weight_label)

        self.weight_box = QComboBox()
        self.weight_box.setFixedWidth(126)
        self.weight_box.setToolTip(
            "Linjebredd i millimeter.\n"
            "Gäller nya objekt – och markerade objekt om du har något markerat.")
        for mm in LINE_WEIGHTS:
            label = f"{mm:.2f}".replace(".", ",") + " mm"
            self.weight_box.addItem(make_weight_icon(mm), label, mm)
        self.weight_box.setCurrentIndex(LINE_WEIGHTS.index(0.25))
        self.weight_box.currentIndexChanged.connect(self._set_weight)
        t2.addWidget(self.weight_box)

        self.ins_btn = QPushButton("Ins.punkt")
        self.ins_btn.setFlat(True)
        self.ins_btn.setCheckable(True)
        self.ins_btn.setChecked(True)
        self.ins_btn.setCursor(Qt.PointingHandCursor)
        self.ins_btn.setToolTip("Visa insättningspunkter för symboler")
        self.ins_btn.toggled.connect(self._set_insert_points)
        t2.addWidget(self.ins_btn)

        self.frame_btn = QPushButton("Textram")
        self.frame_btn.setFlat(True)
        self.frame_btn.setCheckable(True)
        self.frame_btn.setChecked(True)
        self.frame_btn.setCursor(Qt.PointingHandCursor)
        self.frame_btn.setToolTip("Visa tunn ram runt texterna")
        self.frame_btn.toggled.connect(self._set_text_frames)
        t2.addWidget(self.frame_btn)

        t2.addSpacing(10)

        # textformatering
        self.font_box = QFontComboBox()
        self.font_box.setCurrentFont(QFont(self.canvas.text_family))
        self.font_box.setFixedWidth(140)
        self.font_box.setToolTip("Typsnitt för ny text")
        self.font_box.currentFontChanged.connect(
            lambda f: setattr(self.canvas, "text_family", f.family()))
        t2.addWidget(self.font_box)

        self.size_box = QSpinBox()
        self.size_box.setRange(1, 500)
        self.size_box.setValue(int(self.canvas.text_height))
        self.size_box.setSuffix(" mm")
        self.size_box.setFixedWidth(76)
        self.size_box.setToolTip("Texthöjd i millimeter")
        self.size_box.valueChanged.connect(self._set_text_size)
        t2.addWidget(self.size_box)

        self.format_buttons = {}
        for key, label, tip in [
            ("bold", "F", "Fet (Ctrl+B)"),
            ("italic", "K", "Kursiv (Ctrl+I)"),
            ("underline", "U", "Understruken (Ctrl+U)"),
            ("strikeout", "ab", "Genomstruken"),
            ("sub", "x₂", "Nedsänkt"),
            ("sup", "x²", "Upphöjd"),
        ]:
            b = QPushButton(label)
            b.setFlat(True)
            b.setCheckable(True)
            b.setFixedWidth(32)
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(tip)
            b.toggled.connect(
                lambda on, k=key: self._toggle_format(k, on))
            t2.addWidget(b)
            self.format_buttons[key] = b

        t2.addStretch()

        self.org_btn = QPushButton("Origo")
        self.org_btn.setFlat(True)
        self.org_btn.setCheckable(True)
        self.org_btn.setChecked(True)
        self.org_btn.setCursor(Qt.PointingHandCursor)
        self.org_btn.setToolTip("Visa nollpunkten i X och Y (F7)")
        self.org_btn.toggled.connect(self._set_show_origin)
        t2.addWidget(self.org_btn)

        self.home_btn = QPushButton("Hörn")
        self.home_btn.setFlat(True)
        self.home_btn.setCursor(Qt.PointingHandCursor)
        self.home_btn.setToolTip(
            "Sätt nollpunkten i nedre vänstra hörnet (Ctrl+H)")
        self.home_btn.clicked.connect(self._origin_home)
        t2.addWidget(self.home_btn)

        self.center_btn = QPushButton("Centrera")
        self.center_btn.setFlat(True)
        self.center_btn.setCursor(Qt.PointingHandCursor)
        self.center_btn.setToolTip("Sätt nollpunkten mitt i ritytan (Ctrl+0)")
        self.center_btn.clicked.connect(self._center_origin)
        t2.addWidget(self.center_btn)

        self.fit_btn = QPushButton("Visa allt")
        self.fit_btn.setFlat(True)
        self.fit_btn.setCursor(Qt.PointingHandCursor)
        self.fit_btn.setToolTip("Zooma så hela ritningen syns (Ctrl+E)")
        self.fit_btn.clicked.connect(self._zoom_fit)
        t2.addWidget(self.fit_btn)

        self.tool_row = self.toolbar2

        # --- statusrad / textruta ---
        self.editor = QTextEdit()
        self.editor.setFixedHeight(70)
        self.editor.setPlaceholderText("Anteckningar om ritningen …")

        # knappar for att avsluta eller avbryta textrutan
        ok_btn = QPushButton("Klar", self.canvas)
        ok_btn.setFixedSize(96, 26)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setToolTip("Spara texten (Esc)")
        ok_btn.clicked.connect(
            lambda: self.canvas._close_text_editor(True))
        ok_btn.setStyleSheet(
            "QPushButton{background:#3b82f6;color:#fff;border:none;"
            "border-radius:4px;font-size:12px;}"
            "QPushButton:hover{background:#2563eb;}")
        ok_btn.hide()
        self.canvas.text_ok_btn = ok_btn

        root.addWidget(self.titlebar)
        root.addWidget(self.menubar)
        root.addWidget(self.tool_row)
        root.addWidget(self.canvas, 1)

        # statusrad under ritytan
        self.statusbar = QWidget()
        self.statusbar.setFixedHeight(24)
        sl = QHBoxLayout(self.statusbar)
        sl.setContentsMargins(10, 0, 10, 0)
        sl.addStretch()
        self.zoom_label = QLabel("")
        sl.addWidget(self.zoom_label)
        root.addWidget(self.statusbar)

        root.addWidget(self.editor)

        # panelen laggs ovanpa ritytan, inte i layouten
        QTimer.singleShot(0, self._place_toolbar)
        self.toolbar.show()
        self.toolbar.raise_()

        self.canvas.selection_changed = self._update_zoom
        self.canvas.on_selection_change = self._sync_toolbar
        self.canvas.on_place_insert = self._place_pending_insert
        self.canvas.on_cancel_insert = self._cancel_pending_insert
        self.canvas.on_place_block_origin = self._place_block_origin
        self.canvas.on_cancel_block_origin = self._cancel_block_origin

        # tunna kanthandtag langs alla fyra sidor och horn
        self.edge_handles = {}
        for zone in ("left", "right", "top", "bottom",
                     "topleft", "topright", "bottomleft", "bottomright"):
            h = EdgeHandle(self, zone)
            h.show()
            h.raise_()
            self.edge_handles[zone] = h
        self._layout_edge_handles()

        self.apply_theme()
        self._build_xref_menu()
        self._build_layer_menu()
        self._build_scale_menu()
        self._build_block_menu()
        self._build_insert_menu()
        self._build_help_menu()
        self._build_shortcuts()
        self._update_zoom()

    # --- flytande verktygspanel ---
    def _place_toolbar(self):
        """Ger panelen sin storlek och ett bra startlager."""
        if not hasattr(self, "toolbar"):
            return
        self.toolbar.adjustSize()
        storlek = self.toolbar.sizeHint()
        self.toolbar.resize(max(400, storlek.width()), storlek.height())
        # lagg den overst i ritytan, strax under menyraden
        if not getattr(self, "_toolbar_placed", False):
            self._toolbar_placed = True
            p = self.canvas.mapToGlobal(self.canvas.rect().topLeft())
            self.toolbar.move(p.x() + 12, p.y() + 10)
        self.toolbar.raise_()

    def toggle_toolbar(self):
        """Visar eller doljer den flytande verktygspanelen."""
        if self.toolbar.isVisible():
            self.toolbar.hide()
            self._flash_status("Verktygspanelen dold")
        else:
            self._place_toolbar()
            self.toolbar.show()
            self.toolbar.raise_()
            self._flash_status("Verktygspanelen visas")

    def reset_toolbar_position(self):
        """Lagger panelen tillbaka pa sin plats."""
        self._toolbar_placed = False
        self._place_toolbar()
        self._flash_status("Verktygspanelen återställd")

    # --- lagermeny ---
    def _build_layer_menu(self):
        menu = QMenu(self)
        self.layer_menu = menu
        self._fill_layer_menu()
        self.layer_btn.setMenu(menu)

    def _fill_layer_menu(self):
        menu = self.layer_menu
        menu.clear()
        c = self.canvas

        # aktivt lager
        sub = menu.addMenu(f"Aktivt lager  ({c.active_layer})")
        grupp = QActionGroup(self)
        grupp.setExclusive(True)
        self.layer_actions = {}
        for lag in c.layers:
            a = sub.addAction(lag.name)
            a.setCheckable(True)
            a.setChecked(c.active_layer == lag.name)
            a.triggered.connect(lambda _, n=lag.name: self.set_active_layer(n))
            grupp.addAction(a)
            self.layer_actions[lag.name] = a

        menu.addSeparator()

        # flytta markerade objekt
        antal = len(c.selection)
        sub = menu.addMenu(
            f"Flytta {antal} markerade hit" if antal
            else "Flytta markerade hit")
        sub.setEnabled(antal > 0)
        for lag in c.layers:
            a = sub.addAction(lag.name)
            a.triggered.connect(
                lambda _, n=lag.name: self.move_selection_to_layer(n))

        # per lager: synligt, last, farg, ta bort
        menu.addSeparator()
        rubrik = menu.addAction("Visa lager  –  bocka för de som ska synas")
        rubrik.setEnabled(False)
        for lag in c.layers:
            antal_pa = sum(1 for e in c.entities if e.layer == lag.name)
            sub = menu.addMenu(f"{lag.name}  ({antal_pa} objekt)")

            a = sub.addAction("Synligt")
            a.setCheckable(True)
            a.setChecked(lag.visible)
            a.triggered.connect(
                lambda on, n=lag.name: self.set_layer_visible(n, on))

            a = sub.addAction("Låst")
            a.setCheckable(True)
            a.setChecked(lag.locked)
            a.triggered.connect(
                lambda on, n=lag.name: self.set_layer_locked(n, on))

            farg = sub.addMenu("Lagerfärg")
            for label, hexv in PALETTE:
                b = farg.addAction(label)
                b.triggered.connect(
                    lambda _, n=lag.name, x=hexv: self.set_layer_color(n, x))

            if lag.name != DEFAULT_LAYER:
                sub.addSeparator()
                b = sub.addAction(f"Ta bort lagret och dess {antal_pa} objekt")
                b.triggered.connect(lambda _, n=lag.name: self.remove_layer(n))

        menu.addSeparator()
        a = menu.addAction("Nytt lager…")
        a.triggered.connect(self.ask_new_layer)

    # --- rullgardinen for att tanda och slacka lager ---
    def _fill_layer_box(self):
        """Fyller rullgardinen med en rad per lager."""
        box = self.layer_box
        box.blockSignals(True)
        box.clear()
        c = self.canvas
        for lag in c.layers:
            antal = sum(1 for e in c.entities if e.layer == lag.name)
            texter = []
            if not lag.visible:
                texter.append("släckt")
            if lag.locked:
                texter.append("låst")
            if lag.name == c.active_layer:
                texter.append("aktiv")
            svans = "  ·  " + ", ".join(texter) if texter else ""
            # färgprov i lagrets egen färg
            ikon = make_color_icon(lag.color, "#888", 16)
            box.addItem(ikon, f"{lag.name}  ({antal}){svans}", lag.name)
            rad = box.model().item(box.count() - 1)
            if rad is not None:
                rad.setCheckable(True)
                rad.setCheckState(Qt.Checked if lag.visible
                                  else Qt.Unchecked)
        # visa det aktiva lagret i rutan
        idx = box.findData(c.active_layer)
        if idx >= 0:
            box.setCurrentIndex(idx)
        box.blockSignals(False)

    def _layer_box_toggle_click(self, index):
        """Klick i bockkolumnen vaxlar synligheten, annars byter lagret."""
        # kolumn 1 ar bocken, kolumn 0 ar fargprovet
        kolumn = self.layer_box.view().currentIndex().column() \
            if hasattr(self.layer_box.view(), "currentIndex") else -1
        if kolumn == 1:
            self._toggle_layer_from_box(index.row())
        else:
            self.set_active_layer(self.layer_box.itemData(index.row()))

    def _layer_box_selected(self, index):
        """Val i rullgardinen: byt aktivt lager."""
        namn = self.layer_box.itemData(index)
        if namn is None:
            return
        if self.canvas.layer(namn) is None:
            return
        if namn != self.canvas.active_layer:
            self.set_active_layer(namn)

    def _toggle_layer_from_box(self, index):
        """Vaxlar synligheten for raden, utan att byta aktivt lager."""
        namn = self.layer_box.itemData(index)
        if namn is None:
            return
        lag = self.canvas.layer(namn)
        if lag is None:
            return
        self.canvas.set_layer_visible(namn, not lag.visible)
        self._after_layer_change()
        self._flash_status(
            f"Lagret {namn} " + ("tänds" if lag.visible else "släcks"))

    def toggle_active_layer_visible(self):
        """Tander eller slacker det aktiva lagret."""
        namn = self.canvas.active_layer
        lag = self.canvas.layer(namn)
        if lag is None:
            return
        self.canvas.set_layer_visible(namn, not lag.visible)
        self._after_layer_change()
        self._flash_status(
            f"Lagret {namn} " + ("tänds" if lag.visible else "släcks"))

    def _after_layer_change(self):
        """Uppdaterar bade rullgardinen och menyn efter en andring."""
        self._fill_layer_box()
        self._fill_layer_menu()

    def set_active_layer(self, name):
        self.canvas.active_layer = name
        self._fill_layer_menu()
        self._fill_layer_box()
        self._flash_status(f"Aktivt lager: {name}")

    def move_selection_to_layer(self, name):
        n = self.canvas.move_selection_to_layer(name)
        self._after_layer_change()
        self._flash_status(f"{n} objekt flyttade till {name}")
        self._update_zoom()

    def set_layer_visible(self, name, on):
        self.canvas.set_layer_visible(name, on)
        self._after_layer_change()
        self._flash_status(f"Lagret {name} " + ("visas" if on else "döljs"))

    def set_layer_locked(self, name, on):
        self.canvas.set_layer_locked(name, on)
        self._after_layer_change()
        self._flash_status(f"Lagret {name} " + ("låst" if on else "olåst"))

    def set_layer_color(self, name, color):
        self.canvas.set_layer_color(name, color)
        self._after_layer_change()

    def ask_new_layer(self):
        namn, ok = QInputDialog.getText(
            self, "Nytt lager", "Lagrets namn:",
            text=f"Lager{len(self.canvas.layers)}")
        if not ok:
            return
        lag = self.canvas.add_layer(namn)
        if lag is None:
            QMessageBox.warning(
                self, "Nytt lager",
                "Namnet är tomt eller redan upptaget.")
            return
        self._after_layer_change()
        self._flash_status(f"Lagret {lag.name} skapat")

    def remove_layer(self, name):
        antal = sum(1 for e in self.canvas.entities if e.layer == name)
        svar = QMessageBox.question(
            self, "Ta bort lager",
            f"Ta bort lagret {name}?\\n\\n"
            f"{antal} objekt på lagret tas också bort.")
        if svar != QMessageBox.Yes:
            return
        self.canvas.remove_layer(name)
        self._after_layer_change()
        self._flash_status(f"Lagret {name} borttaget")
        self._update_zoom()
        self._update_history_buttons()
        self._fill_layer_menu()
        self._fill_layer_box()

    # --- skalmeny ---
    def _build_scale_menu(self):
        menu = QMenu(self)
        self.scale_menu = menu
        self._fill_scale_menu()
        self.scale_btn.setMenu(menu)

    def _fill_scale_menu(self):
        menu = self.scale_menu
        menu.clear()

        sub = menu.addMenu(f"Ritningsskala  (1:{self.canvas.draw_scale})")
        group = QActionGroup(self)
        group.setExclusive(True)
        self.scale_actions = {}
        for n in SCALE_CHOICES:
            a = sub.addAction(f"1:{n}" if n > 1 else f"{n}:1")
            a.setCheckable(True)
            a.setChecked(self.canvas.draw_scale == n)
            a.triggered.connect(lambda _, x=n: self.set_draw_scale(x))
            group.addAction(a)
            self.scale_actions[n] = a

        sub = menu.addMenu(f"Utskriftsskala  (1:{self.canvas.print_scale})")
        group2 = QActionGroup(self)
        group2.setExclusive(True)
        self.print_actions = {}
        for n in SCALE_CHOICES:
            a = sub.addAction(f"1:{n}" if n > 1 else f"{n}:1")
            a.setCheckable(True)
            a.setChecked(self.canvas.print_scale == n)
            a.triggered.connect(lambda _, x=n: self.set_print_scale(x))
            group2.addAction(a)
            self.print_actions[n] = a

        menu.addSeparator()
        a = menu.addAction("Egen ritningsskala…")
        a.triggered.connect(self.ask_draw_scale)

    def set_draw_scale(self, n):
        self.canvas.draw_scale = n
        self._fill_scale_menu()
        self._update_zoom()
        self._flash_status(f"Ritningsskala 1:{n}")

    def set_print_scale(self, n):
        self.canvas.print_scale = n
        self._fill_scale_menu()
        self._update_zoom()
        self._flash_status(f"Utskriftsskala 1:{n}")

    def ask_draw_scale(self):
        n, ok = QInputDialog.getInt(
            self, "Ritningsskala",
            "Ritningens skala, som 1:n. Ange n:", self.canvas.draw_scale,
            1, 10000)
        if ok:
            self.set_draw_scale(n)

    # --- blockmeny ---
    def _build_block_menu(self):
        menu = QMenu(self)
        self.block_menu = menu
        self._fill_block_menu()
        self.block_btn.setMenu(menu)

    def _fill_block_menu(self):
        menu = self.block_menu
        menu.clear()

        if self.canvas.editing_block is not None:
            name = self.canvas.editing_block.name
            a = menu.addAction(f"Spara ändringen i {name}")
            a.triggered.connect(self.finish_block_edit)
            a = menu.addAction("Avbryt redigeringen")
            a.triggered.connect(self.cancel_block_edit)
            menu.addSeparator()

        a = menu.addAction("Skapa block av markeringen…")
        a.setShortcut(QKeySequence("Ctrl+B"))
        a.triggered.connect(self.create_block_from_selection)
        a = menu.addAction("Skapa block, välj insättningspunkt…")
        a.triggered.connect(
            lambda: self.create_block_from_selection(ask_point=True))

        # losa upp markerade block
        antal = sum(1 for e in self.canvas.selection
                    if isinstance(e, Insert))
        a = menu.addAction(
            f"Lös upp markerat block ({antal} st)" if antal
            else "Lös upp markerat block")
        a.setEnabled(antal > 0)
        a.triggered.connect(self.explode_selection)

        # mina egna block, med val for att andra dem
        egna = [b for b in self.canvas.blocks if b not in builtin_blocks()]
        if egna:
            menu.addSeparator()
            for blk in egna:
                n = blk.count_instances(self.canvas.entities)
                sub = menu.addMenu(f"{blk.name}  ({n} platser)")
                b = sub.addAction("Redigera blocket…")
                b.triggered.connect(lambda _, x=blk: self.start_block_edit(x))
                b = sub.addAction("Placera en till")
                b.triggered.connect(lambda _, x=blk: self._pick_symbol(x))
                b = sub.addAction("Ta bort blocket")
                b.triggered.connect(lambda _, x=blk: self.remove_block(x))

    # --- xref-meny ---
    def _build_xref_menu(self):
        menu = QMenu(self)
        self.xref_menu = menu
        self._fill_xref_menu()
        self.xref_btn.setMenu(menu)

    def _fill_xref_menu(self):
        menu = self.xref_menu
        menu.clear()

        a = menu.addAction("Lägg till bakgrundsritning…")
        a.triggered.connect(self.add_xref)

        if self.canvas.xrefs:
            menu.addSeparator()
            for xr in list(self.canvas.xrefs):
                sub = menu.addMenu(xr.name)
                b = sub.addAction("Ta bort")
                b.triggered.connect(lambda _, x=xr: self.remove_xref(x))
                c = sub.addAction("Zooma till den")
                c.triggered.connect(lambda _, x=xr: self.zoom_to_xref(x))

        if self.canvas.xrefs:
            menu.addSeparator()
            a = menu.addAction("Visa bakgrunder")
            a.setCheckable(True)
            a.setChecked(self.canvas.xref_visible)
            a.triggered.connect(self._toggle_xrefs)

            a = menu.addAction("Ta bort alla bakgrunder")
            a.triggered.connect(self.clear_xrefs)

    def add_xref(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Välj bakgrundsritning", "", "DXF (*.dxf)")
        if not path:
            return
        parsed = self._read_dxf_file(path)
        if parsed is None:
            return
        if not parsed:
            QMessageBox.information(
                self, "Xref",
                "Hittade inga entiteter jag känner igen i filen.")
            return
        self.canvas.add_xref(path, parsed)
        self._fill_xref_menu()
        self._update_zoom()

    def remove_xref(self, xref):
        self.canvas.remove_xref(xref)
        self._fill_xref_menu()
        self._update_zoom()

    def clear_xrefs(self):
        self.canvas.clear_xrefs()
        self._fill_xref_menu()
        self._update_zoom()

    def _toggle_xrefs(self, on):
        self.canvas.xref_visible = on
        self.canvas.update()

    def zoom_to_xref(self, xref):
        x0, y0, x1, y1 = xref.bounds()
        self._zoom_to_box(x0, y0, x1, y1)

    def _zoom_to_box(self, x0, y0, x1, y1):
        c = self.canvas
        w = max(1e-6, x1 - x0)
        h = max(1e-6, y1 - y0)
        pad = 40
        c.scale = max(0.05, min(50.0,
                                min((c.width() - 2 * pad) / w,
                                    (c.height() - 2 * pad) / h)))
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        c.origin = QPointF(c.width() / 2 - cx * c.scale,
                           c.height() / 2 + cy * c.scale)
        c.update()
        self._update_zoom()

    # --- satte in ritning ---
    def _build_insert_menu(self):
        menu = QMenu(self)
        a = menu.addAction("Välj ritning och sätt in…")
        a.triggered.connect(lambda: self.start_insert_dxf(False))
        a = menu.addAction("Sätt in vid punkt i filen…")
        a.triggered.connect(lambda: self.start_insert_dxf(True))
        self.insert_menu = menu
        self.insert_btn.setMenu(menu)

    def _read_dxf_file(self, path):
        """Laser en DXF-fil och returnerar entiteter, eller None vid fel."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as err:
            QMessageBox.warning(self, "Kunde inte öppna", str(err))
            return None
        return parse_dxf(text, self.canvas.blocks)

    def start_insert_dxf(self, ask_point):
        """Valjer en fil och satter in den. Punkten valjs i filen eller med musen."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Välj ritning att sätta in", "", "DXF (*.dxf)")
        if not path:
            return
        parsed = self._read_dxf_file(path)
        if parsed is None:
            return
        if not parsed:
            QMessageBox.information(
                self, "Sätt in",
                "Hittade inga entiteter jag känner igen i filen.")
            return

        self.insert_ok = self._ask_insert_point(path, parsed, ask_point)

    def _ask_insert_point(self, path, parsed, ask_point):
        """Fragar efter insattningspunkten, eller slapper den till musen."""
        if not ask_point:
            # fraga i en dialog i stallet for med musen
            dlg = QInputDialog(self)
            dlg.setWindowTitle("Insättningspunkt")
            dlg.setLabelText("X och Y i millimeter (t.ex. 100, 50):")
            dlg.setTextValue("0, 0")
            if dlg.exec() != QInputDialog.Accepted:
                return False
            try:
                parts = dlg.textValue().replace(";", ",").split(",")
                tx, ty = float(parts[0]), float(parts[1])
            except (ValueError, IndexError):
                QMessageBox.warning(self, "Insättningspunkt",
                                    "Kunde inte läsa talen.")
                return False
            self._place_parsed(parsed, QPointF(tx, ty))
            return True

        # peka med musen
        self._pending_insert = parsed
        self.canvas.set_tool("sattin")
        QMessageBox.information(
            self, "Sätt in",
            f"Klicka i ritytan där {os.path.basename(path)} ska sättas in.\n\n"
            "Esc avbryter.")
        return True

    def _place_pending_insert(self, target):
        """Klick i ritytan placerar den inlästa ritningen."""
        parsed = getattr(self, "_pending_insert", None)
        if not parsed:
            return False
        self._place_parsed(parsed, target)
        self._pending_insert = None
        return True

    def _cancel_pending_insert(self):
        if getattr(self, "_pending_insert", None) is not None:
            self._pending_insert = None

    def _place_parsed(self, parsed, target):
        """Flyttar en inlast ritning sa att dess nedre vanstra hornnar target."""
        x0 = min(e.bounds()[0] for e in parsed)
        y0 = min(e.bounds()[1] for e in parsed)
        dx, dy = target.x() - x0, target.y() - y0
        for ent in parsed:
            ent.translate(dx, dy)
        self.canvas.entities.extend(parsed)
        self.canvas.selection = list(parsed)
        self.canvas.mark([("add", e) for e in parsed])
        self.canvas.update()
        self.canvas.sync_toolbar()
        self._update_zoom()

    # --- symbolmeny ---
    def _build_symbol_menu(self):
        """Symbolmenyn, grupperad sa den gar att overskada."""
        menu = QMenu(self)
        grupper = [
            ("El", EL_SYMBOLS),
            ("Bygg", RIT_SYMBOLS),
        ]
        kanda = set()
        for rubrik, namn in grupper:
            blk_lista = [b for b in self.canvas.blocks if b.name in namn]
            if not blk_lista:
                continue
            sub = menu.addMenu(rubrik)
            for blk in blk_lista:
                a = sub.addAction(blk.name.capitalize())
                a.triggered.connect(lambda _, b=blk: self._pick_symbol(b))
                kanda.add(blk.name)
        # egna block, och allt annat, sist
        ovriga = [b for b in self.canvas.blocks if b.name not in kanda]
        if ovriga:
            sub = menu.addMenu("Egna och övriga")
            for blk in ovriga:
                a = sub.addAction(blk.name.capitalize())
                a.triggered.connect(lambda _, b=blk: self._pick_symbol(b))
        self.symbol_btn.setMenu(menu)

    def _pick_symbol(self, blk):
        self.canvas.mode = None
        self.canvas.set_tool("symbol")
        self.canvas.symbol_to_place = blk
        self.canvas.buttons["symbol"].setChecked(True)

    # --- rutnat ---
    def _set_grid_step(self, value):
        self.canvas.grid_step = value
        self.canvas.update()

    def _pick_color_index(self, index):
        """Farg vald i rullgardinen."""
        color = self.color_box.itemData(index)
        self.canvas.set_selection_color(color)
        if self.canvas.selection:
            self._flash_status(
                f"Färg {self.color_box.currentText()} på "
                f"{len(self.canvas.selection)} objekt")
            self._update_zoom()
        else:
            self._flash_status(
                f"Färg {self.color_box.currentText()} för nya objekt")

    def _pick_color(self, color):
        """Satter farg pa markerade objekt, annars pa nya objekt."""
        self.canvas.set_selection_color(color)
        self._show_color(color)

    def _sync_toolbar(self):
        """Visar markerat objekts farg och bredd i verktygsraden."""
        sel = self.canvas.selection
        color = sel[0].color if sel else self.canvas.draw_color
        lw = sel[0].lw if sel else self.canvas.line_weight
        self._show_color(color)
        self._show_weight(lw)

    def _show_weight(self, lw):
        """Visar en bredd i rullgardinen, aven om den inte finns i listan."""
        self.weight_box.blockSignals(True)
        idx = self.weight_box.findData(lw)
        if idx < 0:
            if lw:
                # bredd som inte finns i listan: lagg till den overst
                for i in range(self.weight_box.count()):
                    if self.weight_box.itemData(i) is None:
                        self.weight_box.removeItem(i)
                        break
                self.weight_box.insertItem(
                    0, make_weight_icon(lw, color=self._icon_color),
                    f"{lw:.2f}".replace(".", ",") + " mm", lw)
                idx = 0
            else:
                idx = self.weight_box.findData(0.25)
        if idx >= 0:
            self.weight_box.setCurrentIndex(idx)
        self.weight_box.blockSignals(False)

    @property
    def _icon_color(self):
        return THEMES[self._resolved()]["icon"]

    def _show_color(self, color):
        """Visar en farg i rullgardinen, aven om den inte finns i listan."""
        self.color_box.blockSignals(True)
        idx = self.color_box.findData(color)
        if idx < 0:
            # farg utanfor listan: lagg till den overst
            while self.color_box.count() > 0 and self.color_box.itemData(0)                     not in [c for _, c in PALETTE]:
                self.color_box.removeItem(0)
            if color:
                self.color_box.insertItem(
                    0, make_color_icon(color, self._icon_color),
                    f"Egen ({color.upper()})", color)
                idx = 0
            else:
                idx = self.color_box.findData(None)
        if idx >= 0:
            self.color_box.setCurrentIndex(idx)
        self.color_box.blockSignals(False)

    def _set_show_origin(self, on):
        self.canvas.show_origin = on
        self.canvas.update()

    def _origin_home(self):
        self.canvas.origin_home()
        self._update_zoom()

    def _center_origin(self):
        self.canvas.center_on_origin()
        self._update_zoom()

    def _zoom_fit(self):
        self.canvas.zoom_to_fit()

    def _set_weight(self, index):
        mm = self.weight_box.itemData(index)
        if mm is None:
            return
        self.canvas.set_selection_weight(mm)
        if self.canvas.selection:
            self._flash_status(
                f"Linjebredd {mm:.2f} mm på {len(self.canvas.selection)} objekt")
            self._update_zoom()
        else:
            self._flash_status(f"Linjebredd {mm:.2f} mm för nya objekt")

    def _set_insert_points(self, on):
        self.canvas.show_insert_points = on
        self.canvas.update()

    def _set_text_frames(self, on):
        self.canvas.text_frames = on
        self.canvas.update()

    def _set_text_size(self, value):
        self.canvas.text_height = float(value)

    def _toggle_format(self, key, on):
        setattr(self.canvas, f"text_{key}", on)
        # nedsankt och upphojd samtidigt ar ingen mening
        if key == "sub" and on:
            self.format_buttons["sup"].setChecked(False)
        elif key == "sup" and on:
            self.format_buttons["sub"].setChecked(False)
        # formateringen slar igenom pa markerad text direkt
        for ent in self.canvas.selection:
            if isinstance(ent, Text):
                if key == "sub":
                    ent.sub, ent.sup = on, False
                elif key == "sup":
                    ent.sup, ent.sub = on, False
                else:
                    setattr(ent, key, on)
        self.canvas.update()

    def _set_snap(self, on):
        self.canvas.grid_snap = on
        self.snap_btn.setToolTip(
            "Fäst punkter till rutnätet (F9) – på" if on
            else "Fäst punkter till rutnätet (F9) – av")

    def toggle_snap(self):
        self.snap_btn.setChecked(not self.snap_btn.isChecked())

    def _set_grid_on(self, on):
        self.canvas.grid_on = on
        self.canvas.update()

    # --- hjalpmenyn ---
    def _build_help_menu(self):
        menu = QMenu(self)
        self.help_menu = menu

        a = menu.addAction("Visa hjälp…")
        a.triggered.connect(self.help)

        menu.addSeparator()
        submenu = menu.addMenu("Tema")
        group = QActionGroup(self)
        group.setExclusive(True)
        self.theme_actions = {}
        for key, label in [("dark", "Mörkt"), ("light", "Ljust"),
                           ("system", "Enligt system")]:
            act = submenu.addAction(label)
            act.setCheckable(True)
            act.setChecked(self.theme_mode == key)
            act.triggered.connect(lambda _, k=key: self.set_theme(k))
            group.addAction(act)
            self.theme_actions[key] = act

        menu.addSeparator()
        a = menu.addAction("Markera allt")
        a.setShortcut(QKeySequence("Ctrl+A"))
        a.triggered.connect(self.select_all)

        a = menu.addAction("Flytta hela ritningen till origo")
        a.triggered.connect(self.move_all_to_origin)

        menu.addSeparator()
        a = menu.addAction("Skapa block av markeringen…")
        a.setShortcut(QKeySequence("Ctrl+B"))
        a.triggered.connect(self.create_block_from_selection)
        a = menu.addAction("Skapa block, välj insättningspunkt…")
        a.triggered.connect(
            lambda: self.create_block_from_selection(ask_point=True))

        menu.addSeparator()
        a = menu.addAction("Lägg till bakgrundsritning…")
        a.triggered.connect(self.add_xref)
        a = menu.addAction("Sätt in ritning vid punkt…")
        a.triggered.connect(lambda: self.start_insert_dxf(False))
        a = menu.addAction("Sätt in ritning genom att peka…")
        a.triggered.connect(lambda: self.start_insert_dxf(True))

        menu.addSeparator()
        a = menu.addAction("Om…")
        a.triggered.connect(self.about)

        self.help_btn.setMenu(menu)

    def _build_shortcuts(self):
        for seq, fn in [
            ("Ctrl+S", self.save_dxf),
            ("Ctrl+Shift+S", self.save_as_dxf),
            ("Ctrl+O", self.open_dxf),
            ("Ctrl+Z", self.undo),
            ("Ctrl+Y", self.redo),
            ("Ctrl+C", self._copy),
            ("Ctrl+X", self._cut),
            ("Ctrl+V", self._paste),
            ("Ctrl+D", self._duplicate),
            ("Ctrl+B", self.create_block_from_selection),
            ("Ctrl+Shift+E", self.explode_selection),
            ("F9", self.toggle_snap),
            ("F7", lambda: self.org_btn.setChecked(
                not self.org_btn.isChecked())),
            ("Ctrl+H", self._origin_home),
            ("Ctrl+0", self._center_origin),
            ("Ctrl+E", self._zoom_fit),
            ("F4", self.toggle_toolbar),
        ]:
            QShortcut(QKeySequence(seq), self, activated=fn)

    # --- tema ---
    def set_theme(self, mode):
        self.theme_mode = mode
        save_settings({"theme": mode})
        self.apply_theme()

    def _resolved(self):
        return system_theme() if self.theme_mode == "system" else self.theme_mode

    def apply_theme(self):
        t = THEMES[self._resolved()]
        self.canvas.apply_theme(t)

        self.titlebar.setStyleSheet(t["titlebar"])
        self.title.setStyleSheet(t["title"])
        self.menubar.setStyleSheet(t["menubar"])
        self.toolbar.bar_color = t["menubar"].split("background:")[1] \
            .split(";")[0]
        self.toolbar.border_color = t["window_border"]
        self.toolbar.update()
        for behallare in (self.toolbar, self.tool_row):
            behallare.setStyleSheet(t["menubar"])
            for knapp in behallare.findChildren(QPushButton):
                knapp.setStyleSheet(t["btn"])
            for ruta in behallare.findChildren(QComboBox):
                ruta.setStyleSheet(t["spin"])
            for ruta in behallare.findChildren(QSpinBox):
                ruta.setStyleSheet(t["spin"])
            for etikett in behallare.findChildren(QLabel):
                etikett.setStyleSheet(t["label"])
        self.tool_row.setFixedHeight(34)
        self.help_btn.setStyleSheet(t["btn"])
        self.xref_btn.setStyleSheet(t["btn"])
        self.insert_btn.setStyleSheet(t["btn"])
        self.block_btn.setStyleSheet(t["btn"])
        self.scale_btn.setStyleSheet(t["btn"])
        self.layer_btn.setStyleSheet(t["btn"])
        self.layer_box.setStyleSheet(t["spin"])
        self.grid_label.setStyleSheet(t["label"])
        self.zoom_label.setStyleSheet(t["label"])
        self.statusbar.setStyleSheet(t["menubar"])
        self.grid_step_box.setStyleSheet(t["spin"])
        self.editor.setStyleSheet(t["editor"])
        if hasattr(self, "help_menu"):
            self.help_menu.setStyleSheet(t["menu"])

        for btn, drawer in self.icon_buttons:
            btn.setIcon(make_icon(drawer, color=t["icon"]))
            btn.setIconSize(QSize(18, 18))
            btn.setStyleSheet(t["btn"])

        for key, btn in self.canvas.buttons.items():
            icon = {
                "linje": draw_line_icon, "rektangel": draw_rect_icon,
                "cirkel": draw_circle_icon, "bage": draw_arc_icon,
                "polylinje": draw_poly_icon, "text": draw_text_icon,
                "symbol": draw_symbol_icon, "skjut": draw_move_icon,
                "markera": draw_select_icon,
            }[key]
            btn.setIcon(make_icon(icon, color=t["icon"]))
            btn.setIconSize(QSize(18, 18))
            btn.setStyleSheet(t["btn"])

        self.grid_btn.setIcon(make_icon(draw_grid, color=t["icon"]))
        self.grid_btn.setIconSize(QSize(18, 18))
        self.grid_btn.setStyleSheet(t["btn"])
        self.snap_btn.setStyleSheet(t["btn"])

        self.weight_label.setStyleSheet(t["label"])
        self.weight_box.setStyleSheet(t["spin"])
        self.color_box.setStyleSheet(t["spin"])
        # rita om provbitarna i temats farg
        for i, mm in enumerate(LINE_WEIGHTS):
            self.weight_box.setItemIcon(i, make_weight_icon(mm, color=t["icon"]))
        self.ins_btn.setStyleSheet(t["btn"])
        self.org_btn.setStyleSheet(t["btn"])
        self.home_btn.setStyleSheet(t["btn"])
        self.center_btn.setStyleSheet(t["btn"])
        self.fit_btn.setStyleSheet(t["btn"])
        self.color_label.setStyleSheet(t["label"])
        self.frame_btn.setStyleSheet(t["btn"])
        self.font_box.setStyleSheet(t["spin"])
        self.size_box.setStyleSheet(t["spin"])
        fmt_style = t["btn"] + (
            "QPushButton{font-family:'Segoe UI';font-size:14px;}"
            "QPushButton:checked{background:#3d3d3d;}"
            if self._resolved() == "dark" else
            "QPushButton{font-family:'Segoe UI';font-size:14px;}"
            "QPushButton:checked{background:#dcdcdc;}"
        )
        for key, btn in self.format_buttons.items():
            btn.setStyleSheet(fmt_style)
            btn.setChecked(getattr(self.canvas, f"text_{key}"))

        clear_btn = self.tool_row.findChildren(QPushButton)[3]
        clear_btn.setIcon(make_icon(draw_trash_icon, color=t["icon"]))
        clear_btn.setIconSize(QSize(18, 18))
        clear_btn.setStyleSheet(t["btn"])

        for btn, drawer, is_close in self.win_buttons:
            btn.setIcon(make_icon(drawer, color=t["icon"]))
            btn.setIconSize(QSize(18, 18))
            if is_close:
                btn.setStyleSheet(
                    "QPushButton{border:none;background:transparent;}"
                    "QPushButton:hover{background:#e81123;}"
                )
            else:
                btn.setStyleSheet(
                    "QPushButton{border:none;background:transparent;}"
                    f"QPushButton:hover{{background:{t['win_hover']};}}"
                )

    # --- fonsterdragning och storleksandring ---
    def _in_drag_zone(self, pos):
        """Titelraden borjar edge_margin in fran kanten."""
        m = self.edge_margin
        bar_h = 32
        return (m <= pos.y() <= m + bar_h
                and m <= pos.x() <= self.width() - m)

    # --- kanten: lyssna pa hela fonstret ---
    # markor per kant, sa man ser vad man tar i
    CURSORS = {
        "left": Qt.SizeHorCursor, "right": Qt.SizeHorCursor,
        "top": Qt.SizeVerCursor, "bottom": Qt.SizeVerCursor,
        "topleft": Qt.SizeFDiagCursor, "bottomright": Qt.SizeFDiagCursor,
        "topright": Qt.SizeBDiagCursor, "bottomleft": Qt.SizeBDiagCursor,
    }

    RESIZE_BAND = 7          # hur brett kanthandtaget ar, i px

    def _edge_at(self, pos):
        """Kant eller horn utifran en punkt i fonstrets koordinater."""
        if self.isMaximized():
            return None
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        b = self.RESIZE_BAND

        left = x <= b
        right = x >= w - b
        top = y <= b
        bottom = y >= h - b

        if top and left:
            return "topleft"
        if top and right:
            return "topright"
        if bottom and left:
            return "bottomleft"
        if bottom and right:
            return "bottomright"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _start_resize(self, zone, global_pos):
        self._resize_zone = zone
        self._resize_start_geo = self.geometry()
        self._resize_start_mouse = global_pos

    def _apply_resize(self, global_pos):
        """Raknar ut ny geometri fran musens rorelse."""
        g0 = self._resize_start_geo
        m0 = self._resize_start_mouse
        dx = global_pos.x() - m0.x()
        dy = global_pos.y() - m0.y()

        x, y, w, h = g0.x(), g0.y(), g0.width(), g0.height()
        min_w = max(520, self.minimumWidth())
        min_h = max(380, self.minimumHeight())
        z = self._resize_zone

        # vansterkant: flytta x och andra bredden
        if "left" in z:
            new_w = max(min_w, w - dx)
            x = x + (w - new_w)
            w = new_w
        # hogerkant
        if "right" in z:
            w = max(min_w, w + dx)
        # overkant
        if "top" in z:
            new_h = max(min_h, h - dy)
            y = y + (h - new_h)
            h = new_h
        # underkant
        if "bottom" in z:
            h = max(min_h, h + dy)

        self.setGeometry(x, y, w, h)

    def mousePressEvent(self, e):
        if e.button() != Qt.LeftButton:
            return
        zone = self._edge_at(e.position())
        if zone is not None:
            self._start_resize(zone, e.globalPosition().toPoint())
            return
        if self._in_drag_zone(e.position()):
            self._drag_pos = (e.globalPosition().toPoint()
                              - self.frameGeometry().topLeft())

    def mouseMoveEvent(self, e):
        if self._resize_zone is not None and e.buttons() & Qt.LeftButton:
            self._apply_resize(e.globalPosition().toPoint())
            return
        if self._drag_pos and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)
            return
        # byt markor nar man star over en kant
        self.setCursor(self.CURSORS.get(self._edge_at(e.position()),
                                        Qt.ArrowCursor))

    def mouseReleaseEvent(self, e):
        self._drag_pos = None
        self._resize_zone = None
        self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, e):
        """Dubbelklick pa titelraden vaxlar mellan normal och maximerad."""
        if getattr(self.canvas, "text_editor", None) is not None:
            return
        if self._in_drag_zone(e.position()):
            self._toggle_max()

    def _toggle_max(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self._sync_margins()

    def _layout_edge_handles(self):
        """Lagger kanthandtagen langs fonstrets kanter."""
        if not getattr(self, "edge_handles", None):
            return
        if self.isMaximized():
            for h in self.edge_handles.values():
                h.hide()
            return

        b = self.RESIZE_BAND          # hur brett handtaget ar
        w, hgt = self.width(), self.height()

        # handtagen ligger langs ytterkanten, i den genomskinliga marginalen
        pos = {
            "left":        (0,          0,          b,  hgt),
            "right":       (w - b,      0,          b,  hgt),
            "top":         (b,          0,          w - 2 * b, b),
            "bottom":      (b,          hgt - b,    w - 2 * b, b),
            "topleft":     (0,          0,          b * 2, b * 2),
            "topright":    (w - b * 2,  0,          b * 2, b * 2),
            "bottomleft":  (0,          hgt - b * 2, b * 2, b * 2),
            "bottomright": (w - b * 2,  hgt - b * 2, b * 2, b * 2),
        }
        for zone, h in self.edge_handles.items():
            x, y, ww, hh = pos[zone]
            h.setGeometry(int(x), int(y), int(max(1, ww)), int(max(1, hh)))
            h.show()
            h.raise_()

    def resizeEvent(self, e):
        self._layout_edge_handles()
        super().resizeEvent(e)

    def _sync_margins(self):
        """Ingen marginal runt ett maximerat fonster."""
        m = 0 if self.isMaximized() else self.edge_margin
        lay = self.centralWidget().layout()
        if lay is not None:
            lay.setContentsMargins(m, m, m, m)

    def changeEvent(self, e):
        if e.type() == e.Type.WindowStateChange:
            self._sync_margins()
            self._layout_edge_handles()
        super().changeEvent(e)

    def showEvent(self, e):
        super().showEvent(e)
        self._layout_edge_handles()

    # --- ritning av fonsterkanten ---
    def paintEvent(self, e):
        """Rundar hornen och drar en 1 px kant runt hela fonstret."""
        t = THEMES[self._resolved()]
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        if self.isMaximized():
            # maximerad: rak kant hela vagen, ingen rundning
            p.fillRect(self.rect(), QColor(t["window_bg"]))
            return

        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, self.corner_radius, self.corner_radius)

        p.fillPath(path, QColor(t["window_bg"]))
        # 2 px kant, sa den gar att se och dra i
        p.setPen(QPen(QColor(t["window_border"]), 2))
        p.drawPath(path)

    # --- angra / gor om ---
    def undo(self):
        if self.canvas.undo():
            self._flash_status("Ångrat")
        else:
            self._flash_status("Det finns inget att ångra")
        self._update_zoom()
        self._update_history_buttons()
        self._fill_layer_menu()
        self._fill_layer_box()

    def redo(self):
        if self.canvas.redo():
            self._flash_status("Gjort om")
        else:
            self._flash_status("Det finns inget att göra om")
        self._update_zoom()
        self._update_history_buttons()
        self._fill_layer_menu()
        self._fill_layer_box()

    def _update_history_buttons(self):
        """Graar ut knapparna nar det inte finns nagot att spola till."""
        if hasattr(self, "undo_btn"):
            self.undo_btn.setEnabled(self.canvas.can_undo())
        if hasattr(self, "redo_btn"):
            self.redo_btn.setEnabled(self.canvas.can_redo())

    def select_all(self):
        self.canvas.select_all()
        self._update_zoom()

    # --- klipp och klistra in ---
    def _copy(self):
        if self.canvas.copy_selection():
            self._flash_status("Kopierat")
        else:
            self._flash_status("Inget markerat att kopiera")

    def _cut(self):
        if self.canvas.cut_selection():
            self._flash_status("Klippt ut")
        else:
            self._flash_status("Inget markerat att klippa ut")

    def _paste(self):
        if self.canvas.paste_clipboard():
            self._flash_status("Inklistrat")
        else:
            self._flash_status("Urklippet är tomt")
        self._update_zoom()

    def _duplicate(self):
        if self.canvas.duplicate_selection():
            self._flash_status("Dubblerat")
        else:
            self._flash_status("Inget markerat att dubblera")

    def _flash_status(self, text):
        """Visar en kort rad i statusfaltet."""
        self.zoom_label.setText(text)

    # --- block ---
    def create_block_from_selection(self, ask_point=False):
        """Gor ett block av markerade objekt."""
        c = self.canvas
        if not c.selection:
            QMessageBox.information(
                self, "Skapa block",
                "Markera först de objekt som ska bli ett block.")
            return

        if ask_point:
            # lat anvandaren peka ut insattningspunkten
            self._pending_block_origin = True
            c.set_tool("blockpunkt")
            QMessageBox.information(
                self, "Skapa block",
                "Klicka i ritytan där blockets insättningspunkt ska vara.\n\n"
                "Esc avbryter.")
            return

        name = self._ask_block_name()
        if not name:
            return
        blk = c.create_block(name)
        if blk is None:
            QMessageBox.warning(
                self, "Skapa block",
                "Namnet är upptaget eller markeringen är tom.")
            return
        self._after_block_created(blk)

    def _ask_block_name(self):
        default = self.canvas.next_block_name()
        text, ok = QInputDialog.getText(
            self, "Skapa block", "Namn på blocket:", text=default)
        if not ok:
            return None
        return text.strip().upper() or None

    def _after_block_created(self, blk):
        self._build_symbol_menu()          # nya blocket syns i menyn
        self._fill_block_menu()
        self._flash_status(f"Blocket {blk.name} skapat")
        self._update_zoom()

    # --- redigera block ---
    def start_block_edit(self, blk):
        if self.canvas.editing_block is not None:
            QMessageBox.information(
                self, "Redigera block",
                "Avsluta den pågående blockredigeringen först.")
            return
        self.canvas.start_block_edit(blk)
        self._fill_block_menu()
        self._flash_status(
            f"Redigerar {blk.name} – ändra delarna, spara i Block-menyn")
        self._update_zoom()

    def finish_block_edit(self):
        blk = self.canvas.finish_block_edit(keep=True)
        if blk is None:
            return
        self._fill_block_menu()
        self._flash_status(f"Blocket {blk.name} uppdaterat")
        self._update_zoom()

    def cancel_block_edit(self):
        blk = self.canvas.cancel_block_edit()
        if blk is None:
            return
        self._fill_block_menu()
        self._flash_status("Blockredigeringen avbruten")
        self._update_zoom()

    def explode_selection(self):
        """Loser upp markerade symboler till vanliga objekt."""
        valda = [e for e in self.canvas.selection if isinstance(e, Insert)]
        if not valda:
            return

        # varna om ett eget block anvands pa fler stallen
        egna = [e for e in valda
                if e.definition not in builtin_blocks()]
        kvar = [e.definition for e in egna
                if e.definition.count_instances(self.canvas.entities) > 1]
        text = (f"Lös upp {len(valda)} block? Delarna blir vanliga objekt "
                f"som går att redigera var för sig.")
        if kvar:
            namn = ", ".join(sorted({b.name for b in kvar}))
            text += (f"\n\n{namn} används på fler ställen. "
                     f"De andra platserna berörs inte.")
        if QMessageBox.question(self, "Lös upp block", text) != QMessageBox.Yes:
            return

        antal = 0
        for ins in valda:
            if self.canvas.explode_insert(ins) is not None:
                antal += 1
        self._build_symbol_menu()
        self._fill_block_menu()
        self._flash_status(f"{antal} block upplöst")
        self._update_zoom()
        self._update_history_buttons()
        self._fill_layer_menu()
        self._fill_layer_box()

    def remove_block(self, blk):
        """Tar bort ett block och alla dess platser."""
        n = blk.count_instances(self.canvas.entities)
        svar = QMessageBox.question(
            self, "Ta bort block",
            f"Ta bort blocket {blk.name}?\n\n"
            f"{n} platser på ritningen tas också bort.")
        if svar != QMessageBox.Yes:
            return
        self.canvas.remove_block(blk)
        self._build_symbol_menu()
        self._fill_block_menu()
        self._flash_status(f"Blocket {blk.name} borttaget")
        self._update_zoom()

    def _place_block_origin(self, model_pt):
        """Klick i ritytan valde insattningspunkten."""
        if not getattr(self, "_pending_block_origin", False):
            return False
        self._pending_block_origin = False
        name = self._ask_block_name()
        if not name:
            return True
        blk = self.canvas.create_block(name, origin=model_pt)
        if blk is None:
            QMessageBox.warning(
                self, "Skapa block",
                "Namnet är upptaget eller markeringen är tom.")
            return True
        self._after_block_created(blk)
        return True

    def _cancel_block_origin(self):
        self._pending_block_origin = False

    def move_all_to_origin(self):
        if not self.canvas.entities:
            return
        xs0 = min(e.bounds()[0] for e in self.canvas.entities)
        ys0 = min(e.bounds()[1] for e in self.canvas.entities)
        self.canvas.move_all_by(-xs0, -ys0)
        self._update_zoom()

    def _update_zoom(self):
        c = self.canvas
        skala = (f"1:{c.draw_scale}" if c.draw_scale > 1
                 else f"{c.draw_scale}:1")
        self.zoom_label.setText(
            f"Zoom {c.scale / 2.0 * 100:.0f} %  ·  "
            f"Skala {skala}  ·  "
            f"{len(c.entities)} entiteter  ·  "
            f"{c.grid_step} enheter/ruta")

    # --- stangning ---
    def has_unsaved(self):
        """Finns osparade andringar?"""
        return bool(self.canvas.changed)

    def _mark_saved(self):
        """Ritningen ar nu sparad, och titeln visar det."""
        self.canvas.changed = False
        namn = os.path.basename(self.path) if self.path else "utan namn"
        self.title.setText(f"CADist 2D Beta – {namn}")

    def _mark_changed(self):
        """Titeln visar att nagot inte ar sparat."""
        if not self.canvas.changed:
            return
        namn = os.path.basename(self.path) if self.path else "utan namn"
        self.title.setText(f"CADist 2D Beta – {namn}  •")

    def maybe_save(self):
        """Fragan som visas nar nagot inte ar sparat.

        Returnerar True om det gar bra att fortsatta (sparat eller
        medvetet utan att spara), False om anvandaren avbrot.
        """
        if not self.has_unsaved():
            return True
        namn = (os.path.basename(self.path) if self.path
                else "Ritningen")
        svar = QMessageBox.question(
            self, "Osparade ändringar",
            f"{namn} har ändringar som inte sparats.\n\n"
            "Vill du spara dem?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save)

        if svar == QMessageBox.Cancel:
            return False
        if svar == QMessageBox.Discard:
            return True
        # Spara: skriv till filen, och kontrollera att det gick
        if self.path:
            return self._write_dxf(self.path)
        path, _ = QFileDialog.getSaveFileName(
            self, "Spara som DXF", "ritning.dxf", "DXF (*.dxf)")
        if not path:
            return False          # avbrott i filvalet = stang inte
        self.path = path
        return self._write_dxf(path)

    def closeEvent(self, e):
        """Fragan om att spara innan fonstret stangs."""
        if self.maybe_save():
            e.accept()
        else:
            e.ignore()

    # --- fil ---
    def save_dxf(self):
        if not self.canvas.entities:
            QMessageBox.information(self, "DXF", "Det finns inget att spara än.")
            return
        if self.path:
            self._write_dxf(self.path)
        else:
            self.save_as_dxf()

    def save_as_dxf(self):
        if not self.canvas.entities:
            QMessageBox.information(self, "DXF", "Det finns inget att spara än.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Spara som DXF", "ritning.dxf", "DXF (*.dxf)")
        if path:
            self.path = path
            self._write_dxf(path)

    def _write_dxf(self, path):
        """Skriver filen. Returnerar True om det gick."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.canvas.to_dxf())
        except OSError as err:
            QMessageBox.warning(self, "Kunde inte spara", str(err))
            return False
        self.path = path
        self._mark_saved()
        self._update_zoom()
        return True

    def open_dxf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Öppna DXF", "", "DXF (*.dxf)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as err:
            QMessageBox.warning(self, "Kunde inte öppna", str(err))
            return

        parsed = parse_dxf(text, self.canvas.blocks)
        if not parsed:
            QMessageBox.information(
                self, "Öppna DXF",
                "Hittade inga entiteter jag känner igen i filen.\n"
                "Programmet läser LINE, LWPOLYLINE, CIRCLE, ARC, TEXT "
                "och INSERT.")
            return

        self.canvas.entities = parsed
        self.path = path
        self.canvas.changed = False
        self.title.setText(f"CADist 2D Beta – {os.path.basename(path)}")
        self.canvas.update()
        self._update_zoom()
        self._update_history_buttons()

    # --- hjalp ---
    def help(self):
        """Visar hjalpen i ett eget fonster: brett, och med rullning."""
        dlg = QDialog(self)
        dlg.setWindowTitle("CADist 2D – hjälp")
        dlg.resize(760, 640)
        dlg.setStyleSheet(THEMES[self._resolved()]["menu"])

        text = QTextEdit()
        text.setReadOnly(True)
        text.setPlainText(HELP_TEXT)
        text.setLineWrapMode(QTextEdit.WidgetWidth)
        text.setMinimumWidth(720)
        text.setStyleSheet(
            "QTextEdit{border:1px solid #d0d0d0;border-radius:4px;"
            "padding:10px;font-size:13px;}")

        box = QVBoxLayout(dlg)
        box.setContentsMargins(12, 12, 12, 12)
        box.addWidget(text, 1)

        knappar = QDialogButtonBox(QDialogButtonBox.Close)
        knappar.rejected.connect(dlg.reject)
        box.addWidget(knappar)

        QShortcut(QKeySequence("Escape"), dlg, activated=dlg.reject)
        dlg.exec()

    def about(self):
        QMessageBox.information(
            self, "Om CADist 2D",
            "CADist 2D – Version 0.1.0 Beta\n\n"
            "Ett 2D-ritprogram med stöd för DXF.\n"
            "Byggt med Python och PySide6 (Qt).\n\n"
            "GitHub: https://github.com/atridium/CADist-2D\n\n"
            "Viktig information – Betaversion\n\n"
            "CADist 2D är under utveckling och kan innehålla fel eller "
            "ofullständiga funktioner.\n\n"
            "Programmet tillhandahålls i befintligt skick, utan garantier, "
            "och används på egen risk.\n\n"
            "Fel kan påverka ritningars geometri, innehåll, måttsättning "
            "och andra uppgifter samt orsaka förlust av data.\n\n"
            "Använd alltid säkerhetskopior av originalfiler och kontrollera "
            "att ritningar och exporterade filer är korrekta innan de "
            "används eller distribueras.\n\n"
            "CADist 2D distribueras under MIT-licensen.")


# ==========================================================================
# Läsning av DXF
# ==========================================================================
def parse_dxf(text, blocks):
    """Laser en DXF-fil med kanda entiteter. Returnerar en lista entiteter."""
    lines = [l.strip() for l in text.splitlines()]
    pairs = []
    for i in range(0, len(lines) - 1, 2):
        try:
            code = int(lines[i])
        except ValueError:
            continue
        pairs.append((code, lines[i + 1]))

    defnum = lambda v: float(v) if v else 0.0

    entities = []
    i = 0
    while i < len(pairs):
        code, value = pairs[i]
        if code == 0 and value in ("LINE", "LWPOLYLINE", "CIRCLE",
                                   "ARC", "TEXT", "INSERT"):
            kind = value
            data = []
            j = i + 1
            while j < len(pairs) and pairs[j][0] != 0:
                data.append(pairs[j])
                j += 1
            i = j
            build_entity(kind, data, entities, blocks, defnum)
        else:
            i += 1
    return entities


def read_common(data, defnum):
    """Laser farg (62), linjebredd (370) och lager (8) ur entitetsdata."""
    color = None
    lw = None
    layer = DEFAULT_LAYER
    for c, v in data:
        if c == 8:
            if v.strip():
                layer = v.strip()
        elif c == 62:
            try:
                color = DXF_INDEX_COLORS.get(int(defnum(v)))
            except Exception:
                color = None
        elif c == 370:
            try:
                mm = float(v) / 100.0
                lw = mm if mm > 0 else None
            except Exception:
                lw = None
    return color, lw, layer


def build_entity(kind, data, entities, blocks, defnum):
    color, lw, layer = read_common(data, defnum)

    def satt(ent):
        ent.layer = layer
        return ent
    def last_x():
        return [defnum(v) for c, v in data if c == 10]

    if kind == "LINE":
        xs = [defnum(v) for c, v in data if c == 10]
        ys = [defnum(v) for c, v in data if c == 20]
        if len(xs) >= 2 and len(ys) >= 2:
            entities.append(satt(Line(QPointF(xs[0], ys[0]),
                                          QPointF(xs[1], ys[1]),
                                          color=color, lw=lw)))

    elif kind == "LWPOLYLINE":
        xs = [defnum(v) for c, v in data if c == 10]
        ys = [defnum(v) for c, v in data if c == 20]
        closed = any(c == 70 and int(defnum(v)) == 1 for c, v in data)
        pts = [QPointF(x, y) for x, y in zip(xs, ys)]
        if len(pts) >= 2:
            if closed and len(pts) == 5 and pts[0] == pts[-1]:
                entities.append(satt(Rect(pts[0], pts[2], color=color, lw=lw)))
            elif closed and len(pts) == 4:
                xs_ = [p.x() for p in pts]
                ys_ = [p.y() for p in pts]
                entities.append(satt(Rect(QPointF(min(xs_), min(ys_)),
                                              QPointF(max(xs_), max(ys_)),
                                              color=color, lw=lw)))
            else:
                entities.append(satt(Polyline(pts, closed, color=color, lw=lw)))

    elif kind == "CIRCLE":
        cx = [defnum(v) for c, v in data if c == 10]
        cy = [defnum(v) for c, v in data if c == 20]
        r = [defnum(v) for c, v in data if c == 40]
        if cx and cy and r:
            entities.append(satt(Circle(QPointF(cx[0], cy[0]), r[0],
                                            color=color, lw=lw)))

    elif kind == "ARC":
        cx = [defnum(v) for c, v in data if c == 10]
        cy = [defnum(v) for c, v in data if c == 20]
        r = [defnum(v) for c, v in data if c == 40]
        s = [defnum(v) for c, v in data if c == 50]
        e = [defnum(v) for c, v in data if c == 51]
        if cx and cy and r:
            entities.append(satt(Arc(QPointF(cx[0], cy[0]), r[0],
                                         s[0] if s else 0.0, e[0] if e else 180.0,
                                         color=color, lw=lw)))

    elif kind == "TEXT":
        cx = [defnum(v) for c, v in data if c == 10]
        cy = [defnum(v) for c, v in data if c == 20]
        h = [defnum(v) for c, v in data if c == 40]
        txt = [v for c, v in data if c == 1]
        if cx and cy and txt:
            entities.append(satt(Text(QPointF(cx[0], cy[0]), txt[0],
                                          h[0] if h else 5.0,
                                          color=color, lw=lw)))

    elif kind == "INSERT":
        name = [v for c, v in data if c == 2]
        cx = [defnum(v) for c, v in data if c == 10]
        cy = [defnum(v) for c, v in data if c == 20]
        rot = [defnum(v) for c, v in data if c == 50]
        sc = [defnum(v) for c, v in data if c == 41]
        if name and cx and cy:
            for blk in blocks:
                if blk.name == name[0]:
                    entities.append(satt(Insert(
                        blk, QPointF(cx[0], cy[0]),
                        rot[0] if rot else 0.0,
                        sc[0] if sc else 1.0,
                        color=color, lw=lw)))
                    break


def main():
    app = QApplication(sys.argv)
    w = DrawingApp()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
