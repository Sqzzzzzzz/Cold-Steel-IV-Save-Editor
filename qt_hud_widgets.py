"""Painted HUD chrome around real, accessible Qt controls.

No screenshot is used as an interface. All coordinates are logical Qt pixels;
the backdrop is scaled once per resize and reused by the glass panels.
"""
from __future__ import annotations

import math
from PySide6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QSize
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPolygonF, QPixmap, QIcon, QFont, QFontMetrics,
)
from PySide6.QtWidgets import (
    QWidget, QFrame, QPushButton, QStyledItemDelegate, QStyle, QLabel,
)
from catalog_core import resource_path


def bevel(rect, cut=7):
    x,y,w,h=rect.x(),rect.y(),rect.width(),rect.height()
    path=QPainterPath()
    path.moveTo(x+cut,y);path.lineTo(x+w-cut,y);path.lineTo(x+w,y+cut)
    path.lineTo(x+w,y+h-cut);path.lineTo(x+w-cut,y+h)
    path.lineTo(x+cut,y+h);path.lineTo(x,y+h-cut);path.lineTo(x,y+cut)
    path.closeSubpath()
    return path


def hud_icon(kind, size=28):
    """Original outlined pictograms; independent of installed symbol fonts."""
    px=QPixmap(size*2,size*2);px.fill(Qt.GlobalColor.transparent)
    p=QPainter(px);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(size*2/28,size*2/28)
    p.setPen(QPen(QColor('#FEE9EC'),1.7,Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    if kind in ('inventory','all'):
        p.drawRoundedRect(QRectF(5,9,18,16),3,3)
        p.drawArc(QRectF(10,2,8,12),0,180*16)
        p.drawLine(10,9,10,23);p.drawLine(18,9,18,23)
        p.drawLine(5,17,23,17);p.drawLine(12,18,16,18)
    elif kind in ('catalog','library','book'):
        path=QPainterPath();path.moveTo(14,6)
        path.cubicTo(10,4,7,4,3,5);path.lineTo(2,23)
        path.cubicTo(6,21,10,21,14,24);path.cubicTo(18,21,22,21,26,23)
        path.lineTo(25,5);path.cubicTo(21,4,18,4,14,6)
        path.closeSubpath();p.drawPath(path);p.drawLine(14,6,14,24)
        p.drawLine(6,8,5,19);p.drawLine(22,8,23,19)
    elif kind=='tools':
        pts=[]
        for n in range(32):
            a=2*math.pi*n/32; r=12 if n%4 in (0,1) else 9
            pts.append(QPointF(14+r*math.cos(a),14+r*math.sin(a)))
        p.setBrush(QColor('#EEDBDE'));p.drawPolygon(QPolygonF(pts))
        p.setBrush(QColor('#3A2F35'));p.drawEllipse(QRectF(10,10,8,8))
    elif kind=='open':
        path=QPainterPath();path.moveTo(3,10);path.lineTo(3,23)
        path.lineTo(23,23);path.lineTo(26,11);path.lineTo(13,11)
        path.lineTo(10,7);path.lineTo(4,7);path.lineTo(3,10)
        p.setBrush(QColor(247,228,230,70));p.drawPath(path)
        p.drawLine(3,12,25,12)
    elif kind=='latest':
        path=QPainterPath();path.moveTo(6,3);path.lineTo(17,3)
        path.lineTo(23,9);path.lineTo(23,25);path.lineTo(6,25)
        path.closeSubpath();p.drawPath(path)
        p.drawLine(17,3,17,9);p.drawLine(17,9,23,9)
        for y in (12,16,20):p.drawLine(10,y,19,y)
    elif kind=='save':
        p.drawRoundedRect(QRectF(4,3,21,23),2,2)
        p.drawRect(QRectF(9,4,11,8));p.drawRect(QRectF(8,17,13,8))
        p.drawLine(17,5,17,10)
    elif kind=='backup':
        p.drawEllipse(QRectF(4,3,20,7))
        for y in (10,15,20):p.drawArc(QRectF(4,y-4,20,8),180*16,180*16)
        p.drawLine(4,6,4,22);p.drawLine(24,6,24,22)
        p.drawArc(QRectF(4,18,20,8),180*16,180*16)
    elif kind=='compare':
        p.drawLine(14,3,14,24);p.drawLine(5,7,23,7);p.drawLine(9,25,19,25)
        for cx in (6,22):
            p.drawLine(cx,7,cx-4,17);p.drawLine(cx,7,cx+4,17)
            p.drawArc(QRectF(cx-4,14,8,7),180*16,180*16)
    elif kind=='check':
        p.setPen(QPen(QColor('#FFEDF0'),3,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        p.drawLine(5,14,11,20);p.drawLine(11,20,23,6)
    elif kind=='remove':
        p.setPen(QPen(QColor('#F8A8AF'),1.8))
        p.drawRect(QRectF(8,9,12,15));p.drawLine(5,6,23,6);p.drawLine(11,3,17,3)
        p.drawLine(12,12,12,21);p.drawLine(16,12,16,21)
    elif kind in ('undo','reset'):
        p.drawArc(QRectF(6,6,17,17),-75*16,285*16)
        p.drawLine(7,6,7,12);p.drawLine(7,12,13,10)
    elif kind=='search':
        p.drawEllipse(QRectF(4,3,15,15));p.drawLine(17,17,25,25)
    elif kind in ('clock','recent'):
        p.drawEllipse(QRectF(3,3,22,22));p.drawLine(14,7,14,14);p.drawLine(14,14,20,17)
    elif kind=='favorites':
        points=[QPointF(14+(12 if i%2==0 else 5)*math.cos(-math.pi/2+i*math.pi/5),
                       14+(12 if i%2==0 else 5)*math.sin(-math.pi/2+i*math.pi/5)) for i in range(10)]
        p.drawPolygon(QPolygonF(points))
    elif kind in ('quartz','quartz_normal','quartz_master','orbment'):
        if kind=='quartz_master':p.drawEllipse(QRectF(4,3,21,22))
        p.drawPolygon(QPolygonF([QPointF(14,3),QPointF(24,12),QPointF(14,25),QPointF(4,12)]))
        p.drawLine(4,12,24,12);p.drawLine(8,6,14,25);p.drawLine(20,6,14,25)
    elif kind in ('equipment','weapon'):
        p.drawPolygon(QPolygonF([QPointF(20,3),QPointF(25,3),QPointF(24,8),QPointF(11,21),QPointF(7,17)]))
        p.drawLine(5,16,13,24);p.drawLine(9,20,3,26)
    elif kind=='armor':
        p.drawPolygon(QPolygonF([QPointF(8,3),QPointF(3,8),QPointF(6,13),QPointF(8,11),QPointF(8,25),QPointF(22,25),QPointF(21,11),QPointF(23,13),QPointF(26,8),QPointF(20,3),QPointF(17,7),QPointF(12,7)]))
        p.drawLine(14,9,14,25)
    elif kind=='shoes':
        for x in (3,15):
            p.drawPolygon(QPolygonF([QPointF(x,5),QPointF(x+7,5),QPointF(x+7,16),QPointF(x+11,19),QPointF(x+10,24),QPointF(x,24)]))
            p.drawLine(x+2,10,x+6,10)
    elif kind in ('accessory','cosmetics'):
        p.drawEllipse(QRectF(5,9,19,17));p.drawPolygon(QPolygonF([QPointF(10,3),QPointF(19,3),QPointF(21,7),QPointF(14,12),QPointF(8,7)]))
    elif kind in ('consumables','consumable','ingredient'):
        p.drawRect(QRectF(10,2,9,5));p.drawLine(11,7,11,11);p.drawLine(18,7,18,11)
        path=QPainterPath();path.moveTo(11,10);path.cubicTo(0,18,7,26,14,26)
        path.cubicTo(23,26,29,17,18,10);p.drawPath(path);p.drawLine(8,18,22,18)
    elif kind=='food':
        p.drawEllipse(QRectF(3,12,22,13));p.drawArc(QRectF(5,5,18,17),0,180*16)
        p.drawLine(14,3,14,6)
    elif kind=='recipe':
        p.drawRect(QRectF(7,3,17,23));p.drawLine(10,8,21,8)
        p.drawLine(10,13,21,13);p.drawLine(10,18,18,18)
    elif kind in ('minimize','maximize','restore','close'):
        if kind=='minimize':p.drawLine(8,18,20,18)
        elif kind=='close':p.drawLine(8,8,20,20);p.drawLine(20,8,8,20)
        elif kind=='maximize':p.drawRect(QRectF(8,7,12,13))
        else:p.drawRect(QRectF(7,10,11,11));p.drawLine(10,7,21,7);p.drawLine(21,7,21,18)
    elif kind=='help':
        p.drawEllipse(QRectF(3,3,22,22));p.drawArc(QRectF(10,7,9,10),-50*16,245*16)
        p.drawLine(14,16,14,18);p.drawPoint(14,22)
    else:
        p.drawPolygon(QPolygonF([QPointF(14,3),QPointF(25,14),QPointF(14,25),QPointF(3,14)]))
    p.end();return QIcon(px)


class HudButton(QPushButton):
    def __init__(self,text='',parent=None):
        super().__init__(text,parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def minimumSizeHint(self):
        # Native QPushButton estimates uncondensed text. Our painted labels can
        # elide; they must not force a compact panel beyond the window edge.
        return QSize(40,28 if self.property('role')=='window' else 40)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        role=self.property('role') or 'normal'
        window=role=='window'
        nav=role=='nav'
        primary=role in ('primary','toolbarPrimary') or self.isChecked()
        hovered=self.underMouse() and self.isEnabled()
        r=QRectF(self.rect()).adjusted(4,4,-4,-4)
        if window:
            if hovered:p.fillRect(self.rect(),QColor('#AF3C54') if self.property('symbol')=='close' else QColor(218,102,113,55))
        elif nav and not self.isChecked():
            g=QLinearGradient(0,0,self.width(),0)
            g.setColorAt(0,QColor(53,42,48,35));g.setColorAt(1,QColor(35,28,32,125))
            p.fillRect(r,g)
            p.setPen(QColor(214,106,116,65));p.drawLine(QPointF(7,r.bottom()),QPointF(r.right(),r.bottom()))
            if hovered:p.fillRect(r,QColor(192,50,63,55))
        else:
            path=bevel(r,12 if nav else 5)
            grad=QLinearGradient(0,r.top(),0,r.bottom())
            if not self.isEnabled():colors=('#392D34','#2D2429','#282025')
            elif role=='danger':colors=('#563C48','#352A3B','#292126')
            elif primary:colors=('#E12B3B','#B8212F','#831821')
            else:colors=('#44373E','#352B31','#2E252A')
            for stop,c in zip((0,.48,1),colors):grad.setColorAt(stop,QColor(c))
            if primary:
                p.setPen(QPen(QColor(240,49,66,24),9));p.drawPath(path)
                p.setPen(QPen(QColor(240,54,70,70),5));p.drawPath(path)
            p.fillPath(path,grad)
            if hovered:p.fillPath(path,QColor(240,100,113,24))
            if self.isDown():p.fillPath(path,QColor(31,25,29,60))
            edge=QColor('#F07D87') if primary else QColor('#CC7685') if role=='danger' else QColor('#CCBCBE')
            if not self.isEnabled():edge=QColor('#4A3C43')
            p.setPen(QPen(QColor(29,23,27,220),3));p.drawPath(path)
            p.setPen(QPen(edge,1.2));p.drawPath(path)
            inset=bevel(r.adjusted(3,3,-3,-3),max(2,9 if nav else 3))
            p.setPen(QPen(QColor(250,231,233,130 if primary else 40),1));p.drawPath(inset)
            glow=QLinearGradient(0,r.top(),0,r.top()+16)
            glow.setColorAt(0,QColor(255,237,240,125 if primary else 25))
            glow.setColorAt(1,QColor(240,131,140,0))
            p.save();p.setClipPath(path);p.fillRect(QRectF(r.left(),r.top(),r.width(),16),glow);p.restore()
        if window:
            if not self.icon().isNull():self.icon().paint(p,QRect((self.width()-23)//2,(self.height()-23)//2,23,23))
            elif self.text():
                f=self.font();f.setPixelSize(19);p.setFont(f);p.setPen(QColor('#E9D7D9'));p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,self.text())
            p.end();return
        f=self.font();f.setPixelSize(17 if nav else 14 if role.startswith('toolbar') else 14);f.setStretch(93)
        f.setWeight(QFont.Weight.Medium if nav else QFont.Weight.Normal)
        if nav:f.setPixelSize(16);f.setStretch(93)
        if role.startswith('toolbar'):f.setStretch(85)
        p.setFont(f)
        text=self.text();icon=self.icon()
        left=role.startswith('toolbar') or nav
        icon_size=34 if nav else 31 if role.startswith('toolbar') else 23
        gap=14 if left else 12
        text_width=max((p.fontMetrics().horizontalAdvance(line) for line in text.split('\n')),default=0)
        if left:x=24 if nav else 19
        else:x=max(9,(self.width()-text_width-(icon_size+gap if not icon.isNull() else 0))//2)
        if not icon.isNull():
            icon.paint(p,QRect(x,(self.height()-icon_size)//2,icon_size,icon_size),mode=QIcon.Mode.Normal if self.isEnabled() else QIcon.Mode.Disabled)
            x+=icon_size+gap
        area=QRect(x,3,max(0,self.width()-x-14),self.height()-6)
        p.setPen(QColor('#F3FAFF') if self.isEnabled() else QColor('#A99B9D'))
        if role=='danger':p.setPen(QColor('#F7AEB8'))
        if '\n' not in text:text=p.fontMetrics().elidedText(text,Qt.TextElideMode.ElideRight,area.width())
        p.drawText(area,Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft,text)
        if self.hasFocus():
            p.setPen(QPen(QColor(255,237,240,175),1,Qt.PenStyle.DotLine));p.drawPath(bevel(r.adjusted(5,5,-5,-5),3))
        p.end()


class AngularTab(QPushButton):
    def __init__(self,text,parent=None):
        super().__init__(text,parent);self.setCheckable(True)
        self.setFixedHeight(51);self.setMinimumWidth(200)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height()
        poly=QPolygonF([QPointF(2,49),QPointF(2,22),QPointF(25,3),QPointF(w-30,3),QPointF(w-3,48)])
        grad=QLinearGradient(0,0,0,h)
        grad.setColorAt(0,QColor('#A3232E') if self.isChecked() else QColor('#382D33'))
        grad.setColorAt(.5,QColor('#8B1F29') if self.isChecked() else QColor('#31272C'))
        grad.setColorAt(1,QColor('#41343B'))
        p.setBrush(grad);p.setPen(QPen(QColor('#DE828B') if self.isChecked() else QColor('#B4A6A7'),1.3));p.drawPolygon(poly)
        p.setPen(QPen(QColor('#FCE8EB'),1));p.drawLine(25,6,w-32,6);p.drawLine(w-30,7,w-8,46)
        if self.isChecked():
            p.setPen(QPen(QColor(240,105,117,80),5));p.drawLine(21,8,w-36,8)
            p.setPen(QPen(QColor('#E1646F'),1));p.drawLine(22,h-6,w-10,h-6)
        p.setFont(self.font());p.setPen(QColor('#F3FBFF'))
        p.drawText(QRect(12,5,w-35,h-5),Qt.AlignmentFlag.AlignCenter,self.text());p.end()


class Backdrop(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.wall=QPixmap(str(resource_path('assets/cs4_cover.jpg')))
        self._scaled_wall=QPixmap()
        self.setAutoFillBackground(False)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if not self.wall.isNull() and self.width()>0 and self.height()>0:
            self._scaled_wall=self.wall.scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatioByExpanding,Qt.TransformationMode.SmoothTransformation)

    def scene_rect(self,pos,size):
        return QRect(pos,size).translated((self._scaled_wall.width()-self.width())//2,(self._scaled_wall.height()-self.height())//2)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(),QColor('#34292F'))
        if not self._scaled_wall.isNull():p.drawPixmap(self.rect(),self._scaled_wall,self.scene_rect(QPoint(0,0),self.size()))
        p.fillRect(self.rect(),QColor(35,28,32,107))
        vignette=QRadialGradient(self.width()*.53,self.height()*.34,self.width()*.75)
        vignette.setColorAt(0,QColor(38,30,35,0));vignette.setColorAt(1,QColor(30,24,28,168))
        p.fillRect(self.rect(),vignette)
        p.save();p.setClipRect(QRect(0,0,210,self.height()))
        _hexes(p,QRectF(0,0,210,self.height()),22,17)
        p.restore()
        p.save();p.setClipRect(QRect(self.width()-280,0,280,self.height()))
        _hexes(p,QRectF(self.width()-280,0,280,self.height()),24,16)
        p.restore()
        # Curved silver frame echoes the reference without obscuring controls.
        sy=self.height()/864
        p.save();p.scale(1,sy)
        curve=QPainterPath();curve.moveTo(91,-25)
        curve.cubicTo(48,120,172,237,160,447)
        curve.cubicTo(154,650,74,714,-42,744)
        metallic=QLinearGradient(62,0,165,0)
        for stop,color in [(0,'#3C3036'),(.24,'#D9DDD4'),(.42,'#F4F3E5'),(.64,'#877D7E'),(1,'#DDCCCE')]:metallic.setColorAt(stop,QColor(color))
        p.setPen(QPen(QColor(34,27,31,190),27));p.drawPath(curve)
        p.setPen(QPen(QBrush(metallic),13));p.drawPath(curve)
        p.setPen(QPen(QColor('#F8F4E7'),2));p.drawPath(curve)
        p.translate(16,0);p.setPen(QPen(QColor('#3A2F35'),5));p.drawPath(curve)
        p.translate(6,0);p.setPen(QPen(QColor(194,98,107,175),1));p.drawPath(curve)
        p.restore();p.end()


def _hexes(p,rect,r=22,alpha=35):
    p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(243,224,227,alpha),.8))
    dy=math.sqrt(3)*r
    for col,x in enumerate(range(int(rect.left())-r,int(rect.right()+r),int(1.5*r))):
        for y in range(int(rect.top())-int(dy),int(rect.bottom()+dy),int(dy)):
            cy=y+(dy/2 if col%2 else 0)
            p.drawPolygon(QPolygonF([QPointF(x+r*math.cos(a*math.pi/3),cy+r*math.sin(a*math.pi/3)) for a in range(6)]))


class GlassPanel(QFrame):
    def __init__(self,parent=None,kind='normal'):
        super().__init__(parent);self.kind=kind
        self.setObjectName('glassPanel');self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self,event):
        if self.kind=='rail':return
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r=QRectF(self.rect()).adjusted(3,3,-4,-4)
        if r.width()<30 or r.height()<30:p.end();return
        path=bevel(r,24 if self.kind=='dark' else 16)
        scene=self.window().centralWidget()
        if isinstance(scene,Backdrop) and not scene._scaled_wall.isNull():
            p.save();p.setClipPath(path)
            p.drawPixmap(self.rect(),scene._scaled_wall,scene.scene_rect(self.mapTo(scene,QPoint(0,0)),self.size()))
            p.restore()
        grad=QLinearGradient(0,0,r.width(),r.height())
        grad.setColorAt(0,QColor(45,36,41,205 if self.kind=='dark' else 213))
        grad.setColorAt(.52,QColor(39,31,35,215 if self.kind=='dark' else 222))
        grad.setColorAt(1,QColor(52,42,48,208))
        p.fillPath(path,grad)
        if self.kind=='dark':
            p.save();p.setClipPath(path)
            _hexes(p,QRectF(r.right()-180,r.top(),180,160),22,18)
            _hexes(p,QRectF(r.left(),r.bottom()-85,190,85),22,20)
            p.restore()
        p.setPen(QPen(QColor(25,20,24,230),5));p.drawPath(path)
        p.setPen(QPen(QColor('#CBBBBD'),1.4));p.drawPath(path)
        p.setPen(QPen(QColor(229,107,118,110),1));p.drawPath(bevel(r.adjusted(4,4,-4,-4),max(6,20 if self.kind=='dark' else 12)))
        p.setPen(QPen(QColor('#F2DFE2'),1.2))
        p.drawLine(QPointF(r.left()+23,r.top()+3),QPointF(r.left()+64,r.top()+3))
        p.drawLine(QPointF(r.right()-23,r.bottom()-3),QPointF(r.right()-70,r.bottom()-3))
        for is_left in (True,False):
            x=r.left() if is_left else r.right();direction=1 if is_left else -1
            p.drawLine(QPointF(x,r.bottom()-24),QPointF(x+20*direction,r.bottom()-4))
            p.drawLine(QPointF(x+3*direction,r.bottom()-25),QPointF(x+22*direction,r.bottom()-6))
        if self.kind=='dark':
            p.setPen(QPen(QColor(240,75,90,60),6));p.drawLine(QPointF(r.left()+28,r.bottom()-1),QPointF(r.right()-26,r.bottom()-1))
            p.setPen(QPen(QColor('#DF727B'),1.4));p.drawLine(QPointF(r.left()+28,r.bottom()-1),QPointF(r.right()-26,r.bottom()-1))
        p.end()


class HudTableDelegate(QStyledItemDelegate):
    """Continuous illuminated rows, with text and icons still supplied by Qt."""
    def paint(self,p,option,index):
        p.save();p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r=option.rect;selected=bool(option.state & QStyle.StateFlag.State_Selected)
        if selected:
            grad=QLinearGradient(0,r.top(),0,r.bottom())
            grad.setColorAt(0,QColor('#CD2534'));grad.setColorAt(.52,QColor('#A61E2A'));grad.setColorAt(1,QColor('#79161F'))
            p.fillRect(r,grad)
            p.setPen(QPen(QColor(240,78,93,80),5));p.drawLine(r.topLeft(),r.topRight());p.drawLine(r.bottomLeft(),r.bottomRight())
            p.setPen(QPen(QColor('#F0808A'),1));p.drawLine(r.topLeft(),r.topRight());p.drawLine(r.bottomLeft(),r.bottomRight())
        else:p.fillRect(r,QColor(57,45,52,174) if index.row()%2 else QColor(37,30,34,85))
        p.setFont(option.font);p.setPen(QColor('#EFF7FC'))
        area=r.adjusted(5,0,-5,0)
        change=index.data(Qt.ItemDataRole.UserRole+1)
        if index.column()==0:
            if selected:
                p.setPen(QPen(QColor('#FFEDF0'),2));p.drawPolyline(QPolygonF([QPointF(r.x()+3,r.center().y()-6),QPointF(r.x()+8,r.center().y()),QPointF(r.x()+3,r.center().y()+6)]))
            ico=index.data(Qt.ItemDataRole.DecorationRole)
            if isinstance(ico,QIcon):ico.paint(p,QRect(r.x()+13,r.y()+2,26,r.height()-4))
            area.setLeft(r.x()+45)
            if change:
                area.setRight(r.right()-15)
                p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#F07882'))
                p.drawEllipse(QPointF(r.right()-7,r.center().y()),2.7,2.7)
                p.setPen(QColor('#EFF7FC'))
            align=Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter
        else:align=Qt.AlignmentFlag.AlignCenter
        if change and index.column()==3:p.setPen(QColor('#F8E5E7'))
        text=str(index.data(Qt.ItemDataRole.DisplayRole) or '')
        text=option.fontMetrics.elidedText(text,Qt.TextElideMode.ElideRight,area.width())
        p.drawText(area,align,text);p.restore()


class ElideLabel(QLabel):
    def __init__(self,text='',parent=None):
        super().__init__(parent);self._full_text='';self.setText(text)

    def setText(self,text):
        self._full_text=text;self.setToolTip(text)
        super().setText(self.fontMetrics().elidedText(text,Qt.TextElideMode.ElideRight,max(1,self.width())))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        super().setText(self.fontMetrics().elidedText(self._full_text,Qt.TextElideMode.ElideRight,max(1,self.width())))


class ItemTitle(QLabel):
    """Wrap long item names without forcing a fixed-width card wider."""
    def __init__(self,parent=None):
        super().__init__(parent);self._full_text='';self._fitting=False
        self.setWordWrap(True);self.setAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

    def setText(self,text):
        self._full_text=text;self.setToolTip(text);self._fit()

    def resizeEvent(self,event):
        super().resizeEvent(event);self._fit()

    def _fit(self):
        if self._fitting:return
        self._fitting=True
        try:
            width=max(40,self.width()-2);height=max(20,self.height())
            font=self.font();font.setWeight(QFont.Weight.DemiBold)
            chosen=14
            for px in range(20,13,-1):
                font.setPixelSize(px);fm=QFontMetrics(font)
                bounds=fm.boundingRect(QRect(0,0,width,1000),Qt.TextFlag.TextWordWrap,self._full_text)
                if bounds.height()<=height and bounds.width()<=width:
                    chosen=px;break
            style=f'font-size:{chosen}px;font-weight:600;'
            if self.styleSheet()!=style:self.setStyleSheet(style)
            font.setPixelSize(chosen);fm=QFontMetrics(font)
            shown=self._full_text
            if fm.boundingRect(QRect(0,0,width,1000),Qt.TextFlag.TextWordWrap,shown).height()>height:
                # Keep the complete string in the tooltip and accessible name.
                lines=[];line=''
                for word in shown.split():
                    candidate=(line+' '+word).strip()
                    if line and fm.horizontalAdvance(candidate)>width:lines.append(line);line=word
                    else:line=candidate
                if line:lines.append(line)
                count=max(1,height//max(1,fm.lineSpacing()))
                if len(lines)>count:
                    lines=lines[:count-1]+[fm.elidedText(' '.join(lines[count-1:]),Qt.TextElideMode.ElideRight,width)]
                shown='\n'.join(lines)
            self.setAccessibleName(self._full_text);super().setText(shown)
        finally:self._fitting=False


class HudTitleBar(QWidget):
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            handle=self.window().windowHandle()
            if handle:handle.startSystemMove()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            w=self.window();w.showNormal() if w.isMaximized() else w.showMaximized()
