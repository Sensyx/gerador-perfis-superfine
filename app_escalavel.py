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
        
        tangentes = {'t1': (t1_x, t1_y), 't2': (t2_x, t2_y), 'v_x': -n_y, 'v_y': n_x}
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
        
        # 1. INTERSECÇÃO VIRTUAL DAS RAMPAS (VÉRTICE)
        y_int = h - h_conn_val
        k = (y_int - t1_y) / v1_y if v1_y != 0 else 0
        x_int = t1_x + k * v1_x
        
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
        
        # 2. CÁLCULO EXATO DO CENTRO DO FILLET
        det = n1_x * n2_y - n1_y * n2_x
        if det != 0:
            dx_c = r_conn * (n2_y - n1_y) / det
            dy_c = r_conn * (n1_x - n2_x) / det
            x_cc = x_int - dx_c
            y_cc = y_int - dy_c
        else:
            x_cc, y_cc = x_int, y_int
            
        t2_x, t2_y = x_cc + r_conn * n1_x, y_cc + r_conn * n1_y
        t3_x_pt, t3_y_pt = x_cc + r_conn * n2_x, y_cc + r_conn * n2_y
        t4_x_pt, t4_y_pt = r_base * n2_x, r_base + r_base * n2_y
        
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
        
        right_half = [(0, h), (x_tr, h)] + arc_top + arc_conn + arc_base + [(0, 0)]
        left_half = [(-x, y) for x, y in reversed(right_half)]
        poly_points = right_half + left_half[1:-1]
        
        tangentes = {
            't1': (t1_x, t1_y), 't2': (t2_x, t2_y),
            't3': (t3_x_pt, t3_y_pt), 't4': (t4_x_pt, t4_y_pt),
            'v1': (x_int - t1_x, y_int - t1_y),
            'v2': (t4_x_pt - x_int, t4_y_pt - y_int)
        }
        return Polygon(poly_points), ang_inf_deg, (x_tr, y_tr, x_cc, y_cc, x_int, y_int), tangentes
    except:
        return None, None, None, None

# ==========================================
# 2. MÓDULOS DE RENDERIZAÇÃO (MATPLOTLIB)
# ==========================================
def formatar_eixos(ax, w, h):
    offset = max(w, h) * 0.15 
    ax.axis('off')
    ax.set_aspect('equal')
    ax.set_xlim(-w/2 - offset*2.5, w/2 + offset*2.5)
    ax.set_ylim(-offset*3, h + offset*4)
    ax.plot([0, 0], [-offset*0.2, h + offset*0.2], color='#ff00ff', lw=0.8, ls='-.')
    return offset

def desenhar_triangular(ax, poly, ang, centros, tangentes, w, h, kwargs):
    r_top, r_base = kwargs['r_top'], kwargs['r_base']
    offset = formatar_eixos(ax, w, h)
    
    x, y = poly.exterior.xy
    ax.plot(x, y, color='black', linewidth=1.5)
    ax.fill(x, y, color='#f0f2f6', alpha=0.5)
    
    xtr1, ytr1 = centros
    ax.plot([-xtr1, xtr1], [ytr1, ytr1], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax.plot([0], [r_base], marker='+', color='#ff00ff', markersize=8, ls='None')
    
    ax.plot([-w/2, -w/2], [h, h + offset*0.5], color='green', lw=0.8, ls='-')
    ax.plot([w/2, w/2], [h, h + offset*0.5], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(-w/2, h + offset*0.4), xytext=(w/2, h + offset*0.4), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(0, h + offset*0.5, f'{w:.2f}', ha='center', va='bottom', fontsize=10, color='green')
    
    ax.plot([xtr1 + 0.2, w/2 + offset*0.6], [h, h], color='green', lw=0.8, ls='-')
    ax.plot([0.2, w/2 + offset*0.6], [0, 0], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(w/2 + offset*0.4, 0), xytext=(w/2 + offset*0.4, h), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(w/2 + offset*0.6, h/2, f'{h:.2f}', ha='left', va='center', fontsize=10, color='green', rotation=90)
    
    ax.annotate(f'R{r_top:.2f}', xy=(-xtr1, ytr1+r_top), xytext=(-w/2 - offset, h + offset*0.2), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    ax.annotate(f'R{r_base:.2f}', xy=(0, 0), xytext=(-offset*1.5, -offset*0.5), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    
    t1_x, t1_y = tangentes['t1']
    t2_x, t2_y = tangentes['t2']
    v_x, v_y = t2_x - t1_x, t2_y - t1_y
    if v_x != 0:
        y_int = t1_y - t1_x * (v_y / v_x)
        y_vis = (t1_y + t2_y) / 2
        x_rampa = t1_x + (y_vis - t1_y) * (v_x / v_y)
        r_arc = math.hypot(x_rampa, y_int - y_vis) # Correção Trigonométrica
        t_arc1, t_arc2 = (90 - ang, 90) if y_int < y_vis else (270, 270 + ang)
        
        ax.add_patch(patches.Arc((0, y_int), r_arc*2, r_arc*2, theta1=t_arc1, theta2=t_arc2, color='green', lw=1))
        mid_ang = math.radians(t_arc1 + ang/2)
        ax.text(r_arc*0.7 * math.cos(mid_ang), y_int + r_arc*0.7 * math.sin(mid_ang), f'({ang:.2f}°)', color='green', fontsize=10, ha='center', va='center', bbox=dict(facecolor='#f0f2f6', edgecolor='none', pad=1, alpha=0.9))

def desenhar_tipo_t(ax, poly, ang, centros, tangentes, w, h, kwargs):
    r_top, r_base, r_conn, h_conn, ang_sup = kwargs['r_top'], kwargs['r_base'], kwargs['r_conn'], kwargs['h_conn'], kwargs['ang_sup']
    offset = formatar_eixos(ax, w, h)
    
    x, y = poly.exterior.xy
    ax.plot(x, y, color='black', linewidth=1.5)
    ax.fill(x, y, color='#f0f2f6', alpha=0.5)
    
    xtr2, ytr2, xcc2, ycc2, x_int, y_int = centros
    t1_x, t1_y = tangentes['t1']
    t2_x, t2_y = tangentes['t2']
    t3_x, t3_y = tangentes['t3']
    t4_x, t4_y = tangentes['t4']
    
    # Marcadores
    ax.plot([-xtr2, xtr2], [ytr2, ytr2], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax.plot([-xcc2, xcc2], [ycc2, ycc2], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax.plot([0], [r_base], marker='+', color='#ff00ff', markersize=8, ls='None')
    
    # EXTENSÕES VIRTUAIS DO VÉRTICE (Para demonstrar a origem da cota)
    ax.plot([-t2_x, -x_int], [t2_y, y_int], color='green', lw=0.8, ls='-')
    ax.plot([-t3_x, -x_int], [t3_y, y_int], color='green', lw=0.8, ls='-')

    # Cotas Lineares
    ax.plot([-w/2, -w/2], [h, h + offset*0.5], color='green', lw=0.8, ls='-')
    ax.plot([w/2, w/2], [h, h + offset*0.5], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(-w/2, h + offset*0.4), xytext=(w/2, h + offset*0.4), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(0, h + offset*0.5, f'{w:.2f}', ha='center', va='bottom', fontsize=10, color='green')
    
    ax.plot([xtr2 + 0.2, w/2 + offset*0.6], [h, h], color='green', lw=0.8, ls='-')
    ax.plot([0.2, w/2 + offset*0.6], [0, 0], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(w/2 + offset*0.4, 0), xytext=(w/2 + offset*0.4, h), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(w/2 + offset*0.6, h/2, f'{h:.2f}', ha='left', va='center', fontsize=10, color='green', rotation=90)
    
    # ALTURA DE TANGÊNCIA (Referenciando EXATAMENTE o Vértice Virtual y_int)
    line_x_h = -w/2 - offset*0.8
    ax.plot([-w/2 + 0.2, line_x_h], [h, h], color='green', lw=0.8, ls='-') 
    ax.plot([-x_int, line_x_h], [y_int, y_int], color='green', lw=0.8, ls='-') 
    ax.annotate('', xy=(line_x_h + 0.2, y_int), xytext=(line_x_h + 0.2, h), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(line_x_h, (h + y_int)/2, f'{h_conn:.2f}', ha='right', va='center', fontsize=10, color='green', rotation=90)
    
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

    # --- COTAS DE ÂNGULO CORRIGIDAS (Hipotenusa e Ancoragem na Reta Física) ---
    v1_x, v1_y = tangentes['v1']
    v2_x, v2_y = tangentes['v2']
    text_bbox = dict(facecolor='#f0f2f6', edgecolor='none', pad=1, alpha=0.9)
    
    if v1_x != 0:
        y_int_sup = t1_y - t1_x * (v1_y / v1_x)
        y_vis_sup = (t1_y + t2_y) / 2 # Metade exata do segmento RETA da peça
        x_rampa_sup = t1_x + (y_vis_sup - t1_y) * (v1_x / v1_y)
        raio_arco_sup = math.hypot(x_rampa_sup, y_int_sup - y_vis_sup) # Correção Pitagórica
        
        ax.add_patch(patches.Arc((0, y_int_sup), raio_arco_sup*2, raio_arco_sup*2, theta1=90-ang_sup, theta2=90, color='green', lw=1))
        ax.text(x_rampa_sup * 0.5, y_vis_sup, f'{ang_sup:.0f}°', color='green', fontsize=10, ha='center', va='center', bbox=text_bbox)

    if v2_x != 0:
        y_int_inf = t3_y - t3_x * (v2_y / v2_x)
        y_vis_inf = (t3_y + t4_y) / 2 # Metade exata do segmento RETA inferior
        x_rampa_inf = t3_x + (y_vis_inf - t3_y) * (v2_x / v2_y)
        raio_arco_inf = math.hypot(x_rampa_inf, y_int_inf - y_vis_inf) # Correção Pitagórica
        
        t1_arc, t2_arc = (90 - ang, 90) if y_int_inf < y_vis_inf else (270, 270 + ang)
        ax.add_patch(patches.Arc((0, y_int_inf), raio_arco_inf*2, raio_arco_inf*2, theta1=t1_arc, theta2=t2_arc, color='green', lw=1))
        ax.text(x_rampa_inf * 0.5, y_vis_inf, f'({ang:.2f}°)', color='green', fontsize=10, ha='center', va='center', bbox=text_bbox)

# ==========================================
# 3. INTERFACE E LÓGICA DINÂMICA
# ==========================================
st.sidebar.header("Estrutura do Projeto")
modo = st.sidebar.radio("Modo de Análise", ["Individual", "Comparativo"])

perfis_disponiveis = ["Triangular", "Tipo T"]

def renderizar_inputs(modelo, prefixo):
    params = {}
    st.markdown(f"**Parâmetros: {modelo}**")
    params['r_top'] = st.number_input("Raio Topo (mm)", value=0.30, step=0.05, format="%.2f", key=f"{prefixo}_rtop")
    params['r_base'] = st.number_input("Raio Base (mm)", value=0.45, step=0.05, format="%.2f", key=f"{prefixo}_rbase")
    
    if modelo == "Tipo T":
        params['r_conn'] = st.number_input("Raio Conexão (mm)", value=0.50, step=0.05, format="%.2f", key=f"{prefixo}_rconn")
        params['h_conn'] = st.number_input("Altura do Vértice Virtual (mm)", value=1.58, step=0.05, format="%.2f", key=f"{prefixo}_hconn")
        params['ang_sup'] = st.number_input("Ângulo Superior (°)", value=39.0, step=0.5, format="%.1f", key=f"{prefixo}_ang")
    
    st.divider()
    return params

with st.sidebar.form("form_dinamico"):
    st.subheader("Medidas Globais")
    w_global = st.number_input("Largura Total (mm)", value=4.20, step=0.10, format="%.2f")
    h_global = st.number_input("Altura Total (mm)", value=10.60, step=0.10, format="%.2f")
    densidade = st.number_input("Densidade (g/cm³)", value=8.50, step=0.10, format="%.2f")
    data_doc = st.date_input("Data de Emissão", value=date.today(), format="DD/MM/YYYY")
    st.divider()
    
    if modo == "Individual":
        perfil_sel = st.selectbox("Selecione a Geometria", perfis_disponiveis)
        kwargs_p1 = renderizar_inputs(perfil_sel, "p1")
    else:
        perfil_1 = st.selectbox("Geometria Esquerda", perfis_disponiveis, index=0)
        kwargs_p1 = renderizar_inputs(perfil_1, "p1")
        
        perfil_2 = st.selectbox("Geometria Direita", perfis_disponiveis, index=1)
        kwargs_p2 = renderizar_inputs(perfil_2, "p2")
        
    submit_button = st.form_submit_button(label="Gerar Documento de Engenharia")

# ==========================================
# GERAÇÃO DA FOLHA (PDF)
# ==========================================
if submit_button or 'app_v12_iniciado' not in st.session_state:
    st.session_state.app_v12_iniciado = True

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

if modo == "Individual":
    poly1, ang1, cent1, tang1 = processar_geometria(perfil_sel, kwargs_p1)
    if poly1 is None:
        st.error("Erro geométrico no perfil.")
    else:
        area = poly1.area
        fig = plt.figure(figsize=(9, 12))
        ax = fig.add_subplot(111)
        plotar_geometria(ax, perfil_sel, poly1, ang1, cent1, tang1, kwargs_p1)
        
        texto_carimbo = f"Superfine Steel Aços Inoxidáveis\nPerfil {perfil_sel}\nÁrea: {area:.3f} mm²\nPeso: {area*densidade:.1f} g/m\nData: {data_doc.strftime('%d/%m/%Y')}"
        ax.text(w_global/2 + max(w_global, h_global)*0.15, h_global, texto_carimbo, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.8'), fontsize=8, family='monospace')
        
        st.pyplot(fig)

elif modo == "Comparativo":
    poly1, ang1, cent1, tang1 = processar_geometria(perfil_1, kwargs_p1)
    poly2, ang2, cent2, tang2 = processar_geometria(perfil_2, kwargs_p2)
    
    if poly1 is None or poly2 is None:
        st.error("Erro geométrico em um dos perfis.")
    else:
        area1, area2 = poly1.area, poly2.area
        reducao = ((area1 - area2) / area1) * 100
        
        fig = plt.figure(figsize=(14, 16))
        fig.subplots_adjust(bottom=0.25, wspace=0.1)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        
        plotar_geometria(ax1, perfil_1, poly1, ang1, cent1, tang1, kwargs_p1)
        ax1.text(0, h_global + max(w_global, h_global)*0.4, f"{area1*densidade:.1f} g/m\nconsiderando densidade {densidade} g/cm³", ha='center', va='center', fontsize=12, bbox=dict(facecolor='white', edgecolor='black', pad=5))
        ax1.text(0, -max(w_global, h_global)*0.3, f"Área\n{area1:.3f} mm²", ha='center', va='center', fontsize=12)
        
        plotar_geometria(ax2, perfil_2, poly2, ang2, cent2, tang2, kwargs_p2)
        ax2.text(0, h_global + max(w_global, h_global)*0.4, f"{area2*densidade:.1f} g/m\nconsiderando densidade {densidade} g/cm³", ha='center', va='center', fontsize=12, bbox=dict(facecolor='white', edgecolor='black', pad=5))
        ax2.text(0, -max(w_global, h_global)*0.3, f"Área\n{area2:.3f} mm²", ha='center', va='center', fontsize=12)
        
        fig.text(0.5, 0.28, f"Redução de {reducao:.2f}%" if reducao > 0 else f"Aumento de {abs(reducao):.2f}%", ha='center', va='center', fontsize=16, fontweight='bold')
        
        ax_carimbo = fig.add_axes([0.1, 0.05, 0.8, 0.15])
        ax_carimbo.axis('off')
        ax_carimbo.add_patch(patches.Rectangle((0, 0), 1, 1, fill=False, lw=1.5, transform=ax_carimbo.transAxes))
        ax_carimbo.plot([0, 1], [0.75, 0.75], color='black', lw=1, transform=ax_carimbo.transAxes)
        ax_carimbo.plot([0, 1], [0.50, 0.50], color='black', lw=1, transform=ax_carimbo.transAxes)
        ax_carimbo.plot([0, 1], [0.25, 0.25], color='black', lw=1, transform=ax_carimbo.transAxes)
        ax_carimbo.plot([0.3, 0.3], [0, 1], color='black', lw=1, transform=ax_carimbo.transAxes)
        ax_carimbo.plot([0.7, 0.7], [0, 1], color='black', lw=1, transform=ax_carimbo.transAxes)
        
        ax_carimbo.text(0.15, 0.875, f"Comparativo {w_global:.2f} x {h_global:.2f}", ha='center', va='center', fontweight='bold', transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.5, 0.875, "-", ha='center', va='center', transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.85, 0.875, "NÃO SE APLICA", ha='center', va='center', transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.15, 0.625, "DENOMINAÇÃO", ha='center', va='center', fontsize=10, transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.5, 0.625, "MATERIAL / DIMENSÕES", ha='center', va='center', fontsize=10, transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.85, 0.625, "TRATAMENTO", ha='center', va='center', fontsize=10, transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.85, 0.375, "Superfine Steel Aços Inoxidáveis", ha='center', va='center', fontweight='bold', color='#1f497d', fontsize=12, transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.85, 0.125, "SANTA BÁRBARA D'OESTE - SP", ha='center', va='center', fontsize=9, transform=ax_carimbo.transAxes)
        
        ax_carimbo.text(0.02, 0.375, "DESENHADO POR:", ha='left', va='center', fontsize=9, transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.15, 0.375, "FELIPE", ha='left', va='center', fontsize=10, fontweight='bold', transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.02, 0.125, "APROVADO POR:", ha='left', va='center', fontsize=9, transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.15, 0.125, "PAULO", ha='left', va='center', fontsize=10, fontweight='bold', transform=ax_carimbo.transAxes)
        
        ax_carimbo.text(0.35, 0.375, "DATA DO DOCUMENTO:", ha='left', va='center', fontsize=9, transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.50, 0.375, f"{data_doc.strftime('%d/%m/%Y')}", ha='left', va='center', fontsize=10, fontweight='bold', transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.35, 0.125, "ESCALA:", ha='left', va='center', fontsize=9, transform=ax_carimbo.transAxes)
        ax_carimbo.text(0.50, 0.125, "3 : 1", ha='left', va='center', fontsize=10, fontweight='bold', transform=ax_carimbo.transAxes)
        
        st.pyplot(fig)

def criar_pdf(figura):
    buf = io.BytesIO()
    figura.savefig(buf, format="pdf", bbox_inches="tight", pad_inches=0.2)
    buf.seek(0)
    return buf

if 'fig' in locals():
    st.sidebar.divider()
    st.sidebar.download_button(
        label="📄 Exportar Documento PDF",
        data=criar_pdf(fig),
        file_name=f"documento_engenharia_{w_global:.2f}x{h_global:.2f}_{data_doc.strftime('%d%m%Y')}.pdf",
        mime="application/pdf"
    )
