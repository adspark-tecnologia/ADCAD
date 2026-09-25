import sys, math
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QAction
from PySide6.QtWidgets import QApplication,QMainWindow,QGraphicsView,QGraphicsScene,QGraphicsLineItem,QGraphicsEllipseItem,QGraphicsRectItem,QToolBar,QFileDialog,QMessageBox,QDockWidget,QListWidget

class View(QGraphicsView):
    def __init__(self, parent):
        super().__init__(parent.scene); self.main=parent; self.start=None; self.preview=None; self.setRenderHint(QPainter.Antialiasing); self.setDragMode(QGraphicsView.NoDrag); self.setMouseTracking(True); self.setBackgroundBrush(QColor('#1c222d')); self.scale(1,-1); self.setSceneRect(-2000,-2000,4000,4000); self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
    def drawBackground(self,p,r):
        super().drawBackground(p,r); p.setPen(QPen(QColor('#29313e'),0)); step=25; left=math.floor(r.left()/step)*step; bottom=math.floor(r.top()/step)*step
        for x in range(left,math.ceil(r.right()/step)*step+1,step): p.drawLine(QPointF(x,r.top()),QPointF(x,r.bottom()))
        for y in range(bottom,math.ceil(r.bottom()/step)*step+1,step): p.drawLine(QPointF(r.left(),y),QPointF(r.right(),y))
        p.setPen(QPen(QColor('#647487'),0)); p.drawLine(QPointF(-2000,0),QPointF(2000,0));p.drawLine(QPointF(0,-2000),QPointF(0,2000))
    def wheelEvent(self,e): self.scale(1.15 if e.angleDelta().y()>0 else 1/1.15,1.15 if e.angleDelta().y()>0 else 1/1.15)
    def mousePressEvent(self,e):
        if e.button()==Qt.MiddleButton: self.setDragMode(QGraphicsView.ScrollHandDrag); super().mousePressEvent(e);return
        if e.button()==Qt.RightButton: self.start=None;self.clear_preview();self.main.statusBar().showMessage('Comando cancelado');return
        if e.button()!=Qt.LeftButton:return super().mousePressEvent(e)
        pt=self.mapToScene(e.position().toPoint()); tool=self.main.tool
        if tool=='select':return super().mousePressEvent(e)
        if tool=='delete':
            item=self.itemAt(e.position().toPoint())
            if item and item in self.main.items:self.main.scene.removeItem(item);self.main.items.remove(item)
            return
        if self.start is None:self.start=pt;return
        self.clear_preview(); self.main.add_shape(tool,self.start,pt); self.start=pt if tool=='polyline' else None
    def mouseMoveEvent(self,e):
        p=self.mapToScene(e.position().toPoint()); self.main.statusBar().showMessage(f'X: {p.x():.2f}  Y: {p.y():.2f}  |  {self.main.tool.upper()}  |  Clique direito para cancelar')
        if self.start is not None:
            self.clear_preview();self.preview=self.main.make_shape(self.main.tool,self.start,p);self.preview.setPen(QPen(QColor('#72d8f5'),0,Qt.DashLine));self.main.scene.addItem(self.preview)
        super().mouseMoveEvent(e)
    def mouseReleaseEvent(self,e):
        if e.button()==Qt.MiddleButton:self.setDragMode(QGraphicsView.NoDrag)
        super().mouseReleaseEvent(e)
    def clear_preview(self):
        if self.preview:self.main.scene.removeItem(self.preview);self.preview=None

class Main(QMainWindow):
    def __init__(self):
        super().__init__();self.setWindowTitle('ADCAD 2D Professional — Protótipo funcional');self.resize(1400,850);self.scene=QGraphicsScene();self.items=[];self.tool='line';self.view=View(self);self.setCentralWidget(self.view);self.statusBar().showMessage('ADCAD pronto — escolha uma ferramenta');self.build_ui()
    def build_ui(self):
        tb=QToolBar('Desenho');tb.setMovable(False);self.addToolBar(tb)
        for label,tool in [('Selecionar','select'),('Linha','line'),('Polilinha','polyline'),('Círculo','circle'),('Retângulo','rect'),('Apagar','delete')]:
            a=QAction(label,self);a.triggered.connect(lambda checked=False,t=tool:self.choose(t));tb.addAction(a)
        tb.addSeparator()
        for label,func in [('Novo',self.new),('Abrir DXF',self.open_dxf),('Salvar DXF',self.save_dxf),('Exportar PDF',self.export_pdf),('Enquadrar',self.fit),('Desfazer',self.undo)]:
            a=QAction(label,self);a.triggered.connect(func);tb.addAction(a)
        dock=QDockWidget('Propriedades / Objetos',self);self.objects=QListWidget();dock.setWidget(self.objects);self.addDockWidget(Qt.LeftDockWidgetArea,dock)
    def choose(self,t):self.tool=t;self.view.start=None;self.view.clear_preview();self.statusBar().showMessage('Ferramenta: '+t)
    def make_shape(self,t,a,b):
        if t in ('line','polyline'):item=QGraphicsLineItem(a.x(),a.y(),b.x(),b.y())
        elif t=='circle':r=math.hypot(b.x()-a.x(),b.y()-a.y());item=QGraphicsEllipseItem(a.x()-r,a.y()-r,2*r,2*r)
        else:item=QGraphicsRectItem(QRectF(a,b).normalized())
        item.setPen(QPen(QColor('#e9edf5'),0));return item
    def add_shape(self,t,a,b):
        item=self.make_shape(t,a,b);self.scene.addItem(item);self.items.append(item);self.objects.addItem(f'{len(self.items)} — {t}');item.setFlag(item.GraphicsItemFlag.ItemIsSelectable,True)
    def new(self):self.scene.clear();self.items=[];self.objects.clear();self.view.start=None;self.view.preview=None
    def undo(self):
        if self.items:self.scene.removeItem(self.items.pop());self.objects.takeItem(self.objects.count()-1)
    def fit(self):
        if self.items:self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-20,-20,20,20),Qt.KeepAspectRatio)
    def save_dxf(self):
        try:import ezdxf
        except ImportError:return QMessageBox.warning(self,'Dependência','Instale ezdxf: pip install ezdxf')
        path,_=QFileDialog.getSaveFileName(self,'Salvar desenho','','DXF (*.dxf)')
        if not path:return
        doc=ezdxf.new('R2010');m=doc.modelspace()
        for i in self.items:
            if isinstance(i,QGraphicsLineItem):l=i.line();m.add_line((l.x1(),l.y1()),(l.x2(),l.y2()))
            elif isinstance(i,QGraphicsEllipseItem):r=i.rect();m.add_circle((r.center().x(),r.center().y()),r.width()/2)
            elif isinstance(i,QGraphicsRectItem):r=i.rect();pts=[(r.left(),r.top()),(r.right(),r.top()),(r.right(),r.bottom()),(r.left(),r.bottom())];m.add_lwpolyline(pts,close=True)
        doc.saveas(path);self.statusBar().showMessage('Salvo: '+path)
    def open_dxf(self):
        try:import ezdxf
        except ImportError:return QMessageBox.warning(self,'Dependência','Instale ezdxf: pip install ezdxf')
        path,_=QFileDialog.getOpenFileName(self,'Abrir desenho','','DXF (*.dxf)')
        if not path:return
        try:
            doc=ezdxf.readfile(path);self.new()
            for e in doc.modelspace():
                if e.dxftype()=='LINE':self.add_shape('line',QPointF(e.dxf.start.x,e.dxf.start.y),QPointF(e.dxf.end.x,e.dxf.end.y))
                elif e.dxftype()=='CIRCLE':self.add_shape('circle',QPointF(e.dxf.center.x,e.dxf.center.y),QPointF(e.dxf.center.x+e.dxf.radius,e.dxf.center.y))
                elif e.dxftype()=='LWPOLYLINE':
                    pts=list(e.get_points('xy'))
                    for a,b in zip(pts,pts[1:]+([pts[0]] if e.closed else [])):self.add_shape('line',QPointF(*a),QPointF(*b))
            self.fit()
        except Exception as ex:QMessageBox.warning(self,'Erro DXF',str(ex))
    def export_pdf(self):
        from PySide6.QtGui import QPdfWriter
        path,_=QFileDialog.getSaveFileName(self,'Exportar PDF','','PDF (*.pdf)')
        if not path:return
        pdf=QPdfWriter(path);pdf.setResolution(150);p=QPainter(pdf);self.scene.render(p,QRectF(0,0,pdf.width(),pdf.height()),self.scene.itemsBoundingRect().adjusted(-20,-20,20,20),Qt.KeepAspectRatio);p.end()
if __name__=='__main__':
    app=QApplication(sys.argv);app.setStyle('Fusion');w=Main();w.show();sys.exit(app.exec())
