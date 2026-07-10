import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon, Point, MultiPolygon
import math
import io
from datetime import date

st.set_page_config(page_title="Gerador de Perfis - Superfine Steel", layout="wide")
st.title("Sistema Paramétrico de Laminação de Perfis")

# ==========================================
# 1. MOTORES MATEMÁTICOS GEOMÉTRICOS
# ==========================================
def gerar_perfil_triangular(w, h, r_top, r_base):
    try:
        x_tr = (w / 2) - r_top
        y_tr = h - r_top
        dx, dy = x_tr, y_tr - r_base
        dist = math.hypot(dx, dy)
        ang_centros = math.atan2(dx, dy)
        ang_tang = math.asin((r_base - r_top) / dist)
        ang_rad = ang_centros - ang_tang
        ang_deg = math.degrees(ang_rad)
        
        canto_sup_esq = Point(-x_tr, y_tr).buffer(r_top, resolution=64)
        canto_sup_dir = Point(x_tr, y_tr).buffer(r_top, resolution=64)
        canto_inf = Point(0, r_base).buffer(r_base, resolution=64)
        poly = MultiPolygon([canto_sup_esq, canto_sup_dir, canto_inf]).convex_hull
        
        n_x, n_y = math.cos(ang_rad), -math.sin(ang_rad)
        t1_x, t1_y = x_tr + r_top * n_x, y_tr + r_top * n_y
        t2_x, t2_y = r_base * n_x, r_base + r_base * n_y
        
        tangentes = {'t1': (t1_x, t1_y), 't2': (t2_x, t2_y)}
        return poly, ang_deg, (x_tr, y_tr), tangentes
    except:
        return None, None, None, None

def gerar_perfil_t_rampas(w, h, r_top, r_base, r_conn, h_conn_val, ang_sup_deg):
    try:
        alpha = math.radians(ang_sup_deg)
        x_tr, y_tr = (w / 2) - r_top, h - r_top
        
        n1_x, n1_y = math.cos(alpha), -math.sin(alpha)
        t1_x, t1_y = x_tr + r_top * n1_x, y_tr + r_top * n1_y
        v1_x, v1_y = -math.sin(alpha), -math.cos(alpha)
        
        # 1. PONTO DE INTERSECÇÃO VIVA DAS RAMPAS (Vértice Fixo para a Cota 1.71)
        y_int = h - h_conn_val
        k = (y_int - t1_y) / v1_y if v1_y != 0 else 0
        x_int = t1_x + k * v1_x
        
        # 2. RAMPA INFERIOR (Tangenciando do Vértice Fixo até a Base)
        dx_v = x_int
        dy_v = y_int - r_base
        dist_v = math.hypot(dx_v, dy_v)
        
        gamma = math.atan2(dy_v, dx_v)
        val = r_base / dist_v
        if val > 1.0: val = 1.0
        elif val < -1.0: val = -1.0
        delta = math.acos(val)
        
        phi = gamma - delta 
        n2_x, n2_y = math.cos(phi), math.sin(phi)
        ang_inf_deg = -math.degrees(phi)
        
        # 3. CÁLCULO EXATO DO CENTRO DO FILLET (Raio de Conexão)
        det = n1_x * n2_y - n1_y * n2_x
        if det != 0:
            dx_c = r_conn * (n2_y - n1_y) / det
            dy_c = r_conn * (n1_x - n2_x) / det
            x_cc = x_int - dx_c
            y_cc = y_int - dy_c
        else:
            x_cc, y_cc = x_int, y_int
            
        t2_x, t2_y = x_cc + r_conn * n1_x, y_cc + r_conn * n1_y
        t3_x, t3_y = x_cc + r_conn * n2_x, y_cc + r_conn * n2_y
        t4_x, t4_y = r_base * n2_x, r_base + r_base * n2_y
        
        def arc(cx, cy, r, a1, a2, cw=True, steps=64):
            pts = []
            if cw:
                while a2 > a1: a2 -= 2*math.pi
            else:
                while a2 < a1: a2 += 2*math.pi
            for i in range(steps + 1):
                ang = a1 + (a2 - a1) * (i / steps)
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
            return pts

        a1_top, a2_top = math.pi / 2, math.atan2(n1_y, n1_x)
        arc_top = arc(x_tr, y_tr, r_top, a1_top, a2_top, cw=True)
        
        a1_conn, a2_conn = math.atan2(-n1_y, -n1_x), math.atan2(-n2_y, -n2_x)
        arc_conn = arc(x_cc, y_cc, r_conn, a1_conn, a2_conn, cw=False) 
        
        a1_base, a2_base = math.atan2(n2_y, n2_x), -math.pi / 2
        arc_base = arc(0, r_base, r_base, a1_base, a2_base, cw=True)
        
        # Montagem do Polígono COM o arco de conexão tangencial
        right_half = [(0, h), (x_tr, h)] + arc_top + arc_conn + arc_base + [(0, 0)]
        left_half = [(-x, y) for x, y in reversed(right_half)]
        poly_points = right_half + left_half[1:-1]
        
        tangentes = {
            't1': (t1_x, t1_y), 't2': (t2_x, t2_y), 
            't3': (t3_x, t3_y), 't4': (t4_x, t4_y),
            't_int': (x_int, y_int)
        }
        return Polygon(poly_points), ang_inf_deg, (x_tr, y_tr, x_cc, y_cc, x_int, y_int), tangentes
    except Exception as e:
        return None, None, None, None

# ==========================================
# 2. MÓDULOS DE RENDERIZAÇÃO E CARIMBO
# ==========================================
def formatar_eixos(ax, w, h):
    offset = max(w, h) * 0.15 
    ax.axis('off')
    ax.set_aspect('equal')
    ax.set_xlim(-w/2 - offset*2.5, w/2 + offset*2.5)
    ax.set_ylim(-offset*3, h + offset*4)
    ax.plot([0, 0], [-offset*0.2, h + offset*0.2], color='#ff00ff', lw=0.8, ls='-.')
    return offset

def desenhar_angulo_tangente(ax, pt_start, pt_end, angulo, pos_ratio=0.5):
    x1, y1 = pt_start
    x2, y2 = pt_end
    v_x, v_y = x2 - x1, y2 - y1
    
    if v_x != 0:
        y_int = y1 - x1 * (v_y / v_x)
        y_vis = y1 + (y2 - y1) * pos_ratio         
        x_rampa = x1 + (y_vis - y1) * (v_x / v_y)
        
        raio_arco = math.hypot(x_rampa, y_vis - y_int)
        
        t1_arc, t2_arc = (90 - angulo, 90) if y_int < y_vis else (270, 270 + angulo)
        ax.add_patch(patches.Arc((0, y_int), raio_arco*2, raio_arco*2, theta1=t1_arc, theta2=t2_arc, color='green', lw=1))
        
        mid_ang = math.radians(t1_arc + angulo/2)
        txt_x = raio_arco * math.cos(mid_ang)
        txt_y = y_int + raio_arco * math.sin(mid_ang)
        
        texto = f'{angulo:.0f}°' if abs(angulo - round(angulo)) < 0.1 else f'({angulo:.2f}°)'
        ax.text(txt_x, txt_y + 0.15, texto, color='green', fontsize=10, ha='center', va='bottom')

def desenhar_triangular(ax, poly, ang, centros, tangentes, w, h, kwargs):
    r_top, r_base = kwargs['r_top'], kwargs['r_base']
    offset = formatar_eixos(ax, w, h)
    gap = 0.15 
    
    x, y = poly.exterior.xy
    ax.plot(x, y, color='black', linewidth=1.5)
    ax.fill(x, y, color='#f0f2f6', alpha=0.5)
    
    xtr1, ytr1 = centros
    ax.plot([-xtr1, xtr1], [ytr1, ytr1], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax.plot([0], [r_base], marker='+', color='#ff00ff', markersize=8, ls='None')
    
    line_y = h + offset*0.4
    ax.plot([-w/2, -w/2], [h, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.plot([w/2, w/2], [h, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(-w/2, line_y), xytext=(w/2, line_y), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(0, line_y + gap, f'{w:.2f}', ha='center', va='bottom', fontsize=10, color='green')
    
    line_x = w/2 + offset*0.5
    ax.plot([xtr1 + 0.2, line_x + 0.2], [h, h], color='green', lw=0.8, ls='-')
    ax.plot([0.2, line_x + 0.2], [0, 0], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(line_x, 0), xytext=(line_x, h), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(line_x - gap, h/2, f'{h:.2f}', ha='center', va='bottom', fontsize=10, color='green', rotation=90)
    
    ax.annotate(f'R{r_top:.2f}', xy=(-xtr1, ytr1+r_top), xytext=(-w/2 - offset, h + offset*0.2), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    ax.annotate(f'R{r_base:.2f}', xy=(0, 0), xytext=(-offset*1.5, -offset*0.5), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    
    desenhar_angulo_tangente(ax, tangentes['t1'], tangentes['t2'], ang, pos_ratio=0.5)

def desenhar_tipo_t(ax, poly, ang, centros, tangentes, w, h, kwargs):
    r_top, r_base, r_conn, h_conn, ang_sup = kwargs['r_top'], kwargs['r_base'], kwargs['r_conn'], kwargs['h_conn'], kwargs['ang_sup']
    offset = formatar_eixos(ax, w, h)
    gap = 0.15 
    
    x, y = poly.exterior.xy
    ax.plot(x, y, color='black', linewidth=1.5)
    ax.fill(x, y, color='#f0f2f6', alpha=0.5)
    
    xtr2, ytr2, xcc2, ycc2, x_int, y_int = centros
    t1_x, t1_y = tangentes['t1']
    t2_x, t2_y = tangentes['t2']
    t3_x, t3_y = tangentes['t3']
    t4_x, t4_y = tangentes['t4']
    t_int_x, t_int_y = tangentes['t_int']
    
    # Marcadores de Centro
    ax.plot([-xtr2, xtr2], [ytr2, ytr2], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax.plot([-xcc2, xcc2], [ycc2, ycc2], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax.plot([0], [r_base], marker='+', color='#ff00ff', markersize=8, ls='None')
    
    # Linhas de Construção do Vértice Fixo (onde as rampas puras se encontrariam)
    ax.plot([-t2_x, -t_int_x], [t2_y, t_int_y], color='green', lw=0.8, ls='-')
    ax.plot([-t3_x, -t_int_x], [t3_y, t_int_y], color='green', lw=0.8, ls='-')
    
    # Cota Horizontal Superior
    line_y = h + offset*0.4
    ax.plot([-w/2, -w/2], [h, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.plot([w/2, w/2], [h, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(-w/2, line_y), xytext=(w/2, line_y), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(0, line_y + gap, f'{w:.2f}', ha='center', va='bottom', fontsize=10, color='green')
    
    # Cota Vertical Lateral (Altura Total)
    line_x = w/2 + offset*0.5
    ax.plot([xtr2 + 0.2, line_x + 0.2], [h, h], color='green', lw=0.8, ls='-')
    ax.plot([0.2, line_x + 0.2], [0, 0], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(line_x, 0), xytext=(line_x, h), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(line_x - gap, h/2, f'{h:.2f}', ha='center', va='bottom', fontsize=10, color='green', rotation=90)
    
    # Cota da Altura do VÉRTICE FIXO (1.71)
    line_x_h = -w/2 - offset*0.8
    ax.plot([-w/2 + 0.2, line_x_h - 0.2], [h, h], color='green', lw=0.8, ls='-') 
    ax.plot([-t_int_x, line_x_h - 0.2], [t_int_y, t_int_y], color='green', lw=0.8, ls='-') 
    ax.annotate('', xy=(line_x_h, t_int_y), xytext=(line_x_h, h), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(line_x_h - 0.2, (h + t_int_y)/2, f'{h_conn:.2f}', ha='center', va='center', fontsize=10, color='green', rotation=90)
    
    # Cotas de Raio
    def get_perimeter_point(cx, cy, r, tx, ty, concave=False):
        d = math.hypot(cx - tx, cy - ty)
        if d == 0: return cx, cy
        ux, uy = (cx - tx)/d, (cy - ty)/d
        return (cx + r * ux, cy + r * uy) if concave else (cx - r * ux, cy - r * uy)

    tx_top, ty_top = -w/2 - offset*0.6, ytr2 + offset*0.4
    px_top, py_top = get_perimeter_point(-xtr2, ytr2, r_top, tx_top, ty_top, False)
    
    tx_conn, ty_conn = -w/2 - offset*0.7, ycc2 - offset*0.4
    px_conn, py_conn = get_perimeter_point(-xcc2, ycc2, r_conn, tx_conn, ty_conn, True)
    
    tx_base, ty_base = -offset*1.5, -offset*0.5
    px_base, py_base = get_perimeter_point(0, r_base, r_base, tx_base, ty_base, False)

    ax.annotate(f'R{r_top:.2f}', xy=(px_top, py_top), xytext=(tx_top, ty_top), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    ax.annotate(f'R{r_conn:.2f}', xy=(px_conn, py_conn), xytext=(tx_conn, ty_conn), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    ax.annotate(f'R{r_base:.2f}', xy=(px_base, py_base), xytext=(tx_base, ty_base), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')

    # Cotas de Ângulo Ancoradas no trecho de Reta FÍSICA de cada rampa
    desenhar_angulo_tangente(ax, (t1_x, t1_y), (t2_x, t2_y), ang_sup, pos_ratio=0.75)
    desenhar_angulo_tangente(ax, (t3_x, t3_y), (t4_x, t4_y), ang, pos_ratio=0.30)

def desenhar_legenda_padrao(fig, titulo, data_str, cliente, responsavel, empresa, obs, area_info=None):
    ax_c = fig.add_axes([0.1, 0.05, 0.8, 0.12]) 
    ax_c.axis('off')
    
    # Bordas e Linhas Principais
    ax_c.add_patch(patches.Rectangle((0, 0), 1, 1, fill=False, lw=1.5, transform=ax_c.transAxes))
    ax_c.plot([0, 1], [0.75, 0.75], color='black', lw=1, transform=ax_c.transAxes)
    ax_c.plot([0, 1], [0.50, 0.50], color='black', lw=1, transform=ax_c.transAxes)
    ax_c.plot([0, 1], [0.25, 0.25], color='black', lw=1, transform=ax_c.transAxes)
    ax_c.plot([0.5, 0.5], [0.25, 1.0], color='black', lw=1, transform=ax_c.transAxes)
    
    v_align = 'center'
    x_lbl_1, x_val_1 = 0.02, 0.22
    x_lbl_2, x_val_2 = 0.52, 0.74
    
    ax_c.text(x_lbl_1, 0.875, "PERFIL/PROJETO:", fontsize=8, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(x_val_1, 0.875, titulo, fontsize=10, transform=ax_c.transAxes, va=v_align)
    ax_c.text(x_lbl_2, 0.875, "EMPRESA:", fontsize=8, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(x_val_2, 0.875, empresa, fontsize=10, transform=ax_c.transAxes, va=v_align)
    
    ax_c.text(x_lbl_1, 0.625, "CLIENTE:", fontsize=8, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(x_val_1, 0.625, cliente, fontsize=10, transform=ax_c.transAxes, va=v_align)
    ax_c.text(x_lbl_2, 0.625, "RESPONSÁVEL:", fontsize=8, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(x_val_2, 0.625, responsavel, fontsize=10, transform=ax_c.transAxes, va=v_align)
    
    ax_c.text(x_lbl_1, 0.375, "DATA DE EMISSÃO:", fontsize=8, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(x_val_1, 0.375, data_str, fontsize=10, transform=ax_c.transAxes, va=v_align)
    
    if area_info:
        ax_c.text(x_lbl_2, 0.375, "ÁREA / PESO LINEAR:", fontsize=8, fontweight='bold', transform=ax_c.transAxes, va=v_align)
        ax_c.text(x_val_2, 0.375, area_info, fontsize=10, transform=ax_c.transAxes, va=v_align)
    
    ax_c.text(x_lbl_1, 0.125, "OBSERVAÇÕES:", fontsize=8, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(0.15, 0.125, obs, fontsize=10, transform=ax_c.transAxes, va=v_align)

# ==========================================
# 3. INTERFACE DE USUÁRIO (TOP-DOWN)
# ==========================================
st.markdown("### 1. Documentação Técnica")
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    empresa = c1.text_input("Empresa", value="Superfine Steel")
    cliente = c2.text_input("Cliente", value="")
    responsavel = c3.text_input("Responsável", value="Felipe Maia")
    data_doc = c4.date_input("Data de Emissão", value=date.today())
    obs = st.text_input("Observação", value="Tolerâncias dimensionais e de usinagem não indicadas devem seguir a norma DIN 7168.")

st.markdown("### 2. Configurações Globais")
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    w_global = c1.number_input("Largura Total (mm)", value=5.30, step=0.10, format="%.2f")
    h_global = c2.number_input("Altura Total (mm)", value=10.60, step=0.10, format="%.2f")
    densidade = c3.number_input("Densidade (g/cm³)", value=8.50, step=0.10, format="%.2f")
    modo = c4.selectbox("Modo de Análise", ["Individual", "Comparativo"])

st.markdown("### 3. Parâmetros Geométricos")
perfis_disponiveis = ["Triangular", "Tipo T"]

def renderizar_inputs(prefixo):
    col1, col2, col3, col4, col5 = st.columns(5)
    r_top = col1.number_input("Raio Topo (mm)", value=0.30, step=0.05, format="%.2f", key=f"{prefixo}_rtop")
    r_base = col2.number_input("Raio Base (mm)", value=0.45, step=0.05, format="%.2f", key=f"{prefixo}_rbase")
    
    if st.session_state.get(f"{prefixo}_sel") == "Tipo T":
        r_conn = col3.number_input("Raio Conexão (mm)", value=0.50, step=0.05, format="%.2f", key=f"{prefixo}_rconn")
        h_conn = col4.number_input("Altura Intersecção (mm)", value=1.71, step=0.05, format="%.2f", key=f"{prefixo}_hconn")
        ang_sup = col5.number_input("Ângulo Superior (°)", value=39.0, step=0.5, format="%.1f", key=f"{prefixo}_ang")
        return {'r_top': r_top, 'r_base': r_base, 'r_conn': r_conn, 'h_conn': h_conn, 'ang_sup': ang_sup}
    return {'r_top': r_top, 'r_base': r_base}

if modo == "Individual":
    perfil_sel = st.selectbox("Selecione a Geometria", perfis_disponiveis, key="p1_sel")
    kwargs_p1 = renderizar_inputs("p1")
else:
    colA, colB = st.columns(2)
    with colA:
        perfil_1 = st.selectbox("Geometria Esquerda", perfis_disponiveis, index=0, key="p1_sel")
        kwargs_p1 = renderizar_inputs("p1")
    with colB:
        perfil_2 = st.selectbox("Geometria Direita", perfis_disponiveis, index=1, key="p2_sel")
        kwargs_p2 = renderizar_inputs("p2")
    
st.divider()
submit_button = st.button("Atualizar Desenho", type="primary", use_container_width=True)

# ==========================================
# 4. GERAÇÃO DA FOLHA (PDF)
# ==========================================
if submit_button or 'app_v22_iniciado' not in st.session_state:
    st.session_state.app_v22_iniciado = True

def processar_geometria(modelo, kwargs):
    if modelo == "Triangular":
        return gerar_perfil_triangular(w_global, h_global, kwargs['r_top'], kwargs['r_base'])
    elif modelo == "Tipo T":
        return gerar_perfil_t_rampas(w_global, h_global, kwargs['r_top'], kwargs['r_base'], kwargs['r_conn'], kwargs['h_conn'], kwargs['ang_sup'])

def plotar_geometria(ax, modelo, poly, ang, centros, tangentes, kwargs):
    if modelo == "Triangular":
        desenhar_triangular(ax, poly, ang, centros, tangentes, w_global, h_global, kwargs)
    elif modelo == "Tipo T":
        desenhar_tipo_t(ax, poly, ang, centros, tangentes, w_global, h_global, kwargs)

titulo_doc = ""

if modo == "Individual":
    titulo_doc = f"Perfil {perfil_sel} {w_global:.2f} x {h_global:.2f}"
    poly1, ang1, cent1, tang1 = processar_geometria(perfil_sel, kwargs_p1)
    if poly1 is None:
        st.error("Erro geométrico no perfil. Verifique as medidas.")
    else:
        area = poly1.area
        peso = area * densidade
        
        fig = plt.figure(figsize=(10, 14))
        ax = fig.add_axes([0.1, 0.25, 0.8, 0.7]) 
        plotar_geometria(ax, perfil_sel, poly1, ang1, cent1, tang1, kwargs_p1)
        
        area_string = f"{area:.3f} mm²  /  {peso:.1f} g/m"
        desenhar_legenda_padrao(fig, titulo_doc, data_doc.strftime('%d/%m/%Y'), cliente, responsavel, empresa, obs, area_string)
        
        st.pyplot(fig)

elif modo == "Comparativo":
    titulo_doc = f"Comparativo {w_global:.2f} x {h_global:.2f}"
    poly1, ang1, cent1, tang1 = processar_geometria(perfil_1, kwargs_p1)
    poly2, ang2, cent2, tang2 = processar_geometria(perfil_2, kwargs_p2)
    
    if poly1 is None or poly2 is None:
        st.error("Erro geométrico em um dos perfis.")
    else:
        area1, area2 = poly1.area, poly2.area
        reducao = ((area1 - area2) / area1) * 100
        
        fig = plt.figure(figsize=(14, 16))
        ax1 = fig.add_axes([0.05, 0.25, 0.4, 0.65])
        ax2 = fig.add_axes([0.55, 0.25, 0.4, 0.65])
        
        plotar_geometria(ax1, perfil_1, poly1, ang1, cent1, tang1, kwargs_p1)
        ax1.text(0, h_global + max(w_global, h_global)*0.4, f"{area1*densidade:.1f} g/m\n(Densidade: {densidade} g/cm³)", ha='center', va='center', fontsize=12, bbox=dict(facecolor='white', edgecolor='black', pad=5))
        ax1.text(0, -max(w_global, h_global)*0.3, f"Área: {area1:.3f} mm²", ha='center', va='center', fontsize=12)
        
        plotar_geometria(ax2, perfil_2, poly2, ang2, cent2, tang2, kwargs_p2)
        ax2.text(0, h_global + max(w_global, h_global)*0.4, f"{area2*densidade:.1f} g/m\n(Densidade: {densidade} g/cm³)", ha='center', va='center', fontsize=12, bbox=dict(facecolor='white', edgecolor='black', pad=5))
        ax2.text(0, -max(w_global, h_global)*0.3, f"Área: {area2:.3f} mm²", ha='center', va='center', fontsize=12)
        
        fig.text(0.5, 0.22, f"Redução de {reducao:.2f}%" if reducao > 0 else f"Aumento de {abs(reducao):.2f}%", ha='center', va='center', fontsize=16, fontweight='bold')
        
        desenhar_legenda_padrao(fig, titulo_doc, data_doc.strftime('%d/%m/%Y'), cliente, responsavel, empresa, obs)
        
        st.pyplot(fig)

def criar_pdf(figura):
    buf = io.BytesIO()
    figura.savefig(buf, format="pdf", bbox_inches="tight", pad_inches=0.2)
    buf.seek(0)
    return buf

if 'fig' in locals():
    st.download_button(
        label="📄 Fazer Download do Documento PDF",
        data=criar_pdf(fig),
        file_name=f"{titulo_doc.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
