import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon, Point, MultiPolygon
import math
import io
from datetime import date

st.set_page_config(page_title="Comparativo de Perfis - Superfine Steel", layout="wide")
st.title("Estudo de Redução: Perfil Triangular vs Tipo T")

st.sidebar.header("Parâmetros Globais")

with st.sidebar.form("form_comparativo"):
    largura_total = st.number_input("Largura Total do Topo (mm)", value=5.30, step=0.10, format="%.2f")
    altura = st.number_input("Altura Total (mm)", value=10.60, step=0.10, format="%.2f")
    
    st.divider()
    st.markdown("**Raios Padrão**")
    raio_topo = st.number_input("Raio do Topo (mm)", value=0.30, step=0.05, format="%.2f")
    raio_base = st.number_input("Raio da Base (mm)", value=0.45, step=0.05, format="%.2f")
    
    st.divider()
    st.markdown("**Exclusivo Perfil T**")
    raio_conn = st.number_input("Raio de Conexão (mm)", value=0.50, step=0.05, format="%.2f")
    h_conn = st.number_input("Altura de Tangência (mm)", value=1.71, step=0.05, format="%.2f")
    angulo_sup = st.number_input("Ângulo Rampa Superior (°)", value=39.0, step=0.5, format="%.1f")
    
    st.divider()
    st.markdown("**Propriedades e Documentação**")
    densidade = st.number_input("Densidade (g/cm³)", value=8.50, step=0.10, format="%.2f")
    data_doc = st.date_input("Data do Documento", value=date.today(), format="DD/MM/YYYY")
    
    submit_button = st.form_submit_button(label="Gerar Estudo Comparativo")

# ==========================================
# MOTOR MATEMÁTICO 1: PERFIL TRIANGULAR (V)
# ==========================================
def gerar_perfil_triangular(w, h, r_top, r_base):
    try:
        x_tr = (w / 2) - r_top
        y_tr = h - r_top
        
        dx = x_tr
        dy = y_tr - r_base
        dist = math.hypot(dx, dy)
        
        ang_centros = math.atan2(dx, dy)
        ang_tang = math.asin((r_base - r_top) / dist)
        
        ang_rad = ang_centros - ang_tang
        ang_deg = math.degrees(ang_rad)
        
        canto_sup_esq = Point(-x_tr, y_tr).buffer(r_top, resolution=64)
        canto_sup_dir = Point(x_tr, y_tr).buffer(r_top, resolution=64)
        canto_inf = Point(0, r_base).buffer(r_base, resolution=64)
        poly = MultiPolygon([canto_sup_esq, canto_sup_dir, canto_inf]).convex_hull
        
        n_x = math.cos(ang_rad)
        n_y = -math.sin(ang_rad)
        
        t1_x = x_tr + r_top * n_x
        t1_y = y_tr + r_top * n_y
        t2_x = 0 + r_base * n_x
        t2_y = r_base + r_base * n_y
        
        tangentes = {'t1': (t1_x, t1_y), 't2': (t2_x, t2_y), 'v_x': -n_y, 'v_y': n_x}
        
        return poly, ang_deg, (x_tr, y_tr), tangentes
    except:
        return None, None, None, None

# ==========================================
# MOTOR MATEMÁTICO 2: PERFIL T RAMPAS
# ==========================================
def gerar_perfil_t_rampas(w, h, r_top, r_base, r_conn, h_conn_val, ang_sup_deg):
    try:
        alpha = math.radians(ang_sup_deg)
        x_tr = (w / 2) - r_top
        y_tr = h - r_top
        
        n1_x = math.cos(alpha)
        n1_y = -math.sin(alpha)
        t1_x = x_tr + r_top * n1_x
        t1_y = y_tr + r_top * n1_y
        v1_x = -math.sin(alpha)
        v1_y = -math.cos(alpha)
        
        t2_y = h - h_conn_val
        k = (t2_y - t1_y) / v1_y if v1_y != 0 else 0
        t2_x = t1_x + k * v1_x
        
        x_cc = t2_x + r_conn * n1_x
        y_cc = t2_y + r_conn * n1_y
        
        dy = y_cc - r_base
        dx = x_cc
        dist = math.hypot(dx, dy)
        
        gamma = math.atan2(dy, dx)
        delta = math.acos((r_base + r_conn) / dist)
        phi = gamma - delta 
        
        n2_x = math.cos(phi)
        n2_y = math.sin(phi)
        ang_inf_deg = -math.degrees(phi)
        
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

        a1_top = math.pi / 2
        a2_top = math.atan2(n1_y, n1_x)
        arc_top = arc(x_tr, y_tr, r_top, a1_top, a2_top, cw=True)
        
        a1_conn = math.atan2(-n1_y, -n1_x)
        a2_conn = math.atan2(-n2_y, -n2_x)
        arc_conn = arc(x_cc, y_cc, r_conn, a1_conn, a2_conn, cw=False) 
        
        a1_base = math.atan2(n2_y, n2_x)
        a2_base = -math.pi / 2
        arc_base = arc(0, r_base, r_base, a1_base, a2_base, cw=True)
        
        right_half = [(0, h), (x_tr, h)] + arc_top + arc_conn + arc_base + [(0, 0)]
        left_half = [(-x, y) for x, y in reversed(right_half)]
        poly_points = right_half + left_half[1:-1]
        
        t3_x_pt = x_cc - r_conn * n2_x
        t3_y_pt = y_cc - r_conn * n2_y
        t4_x_pt = r_base * n2_x
        t4_y_pt = r_base + r_base * n2_y
        
        tangentes = {
            't1': (t1_x, t1_y), 'v1': (t2_x - t1_x, t2_y - t1_y),
            't3': (t3_x_pt, t3_y_pt), 'v2': (t4_x_pt - t3_x_pt, t4_y_pt - t3_y_pt)
        }
        return Polygon(poly_points), ang_inf_deg, (x_tr, y_tr, x_cc, y_cc, t2_x, t2_y), tangentes
    except:
        return None, None, None, None

# ==========================================
# RENDERIZAÇÃO MESTRA
# ==========================================
if submit_button or 'comparativo_gerado' not in st.session_state:
    st.session_state.comparativo_gerado = True

poly_tri, ang_tri, cent_tri, tang_tri = gerar_perfil_triangular(largura_total, altura, raio_topo, raio_base)
poly_t, ang_t, cent_t, tang_t = gerar_perfil_t_rampas(largura_total, altura, raio_topo, raio_base, raio_conn, h_conn, angulo_sup)

if poly_tri is None or poly_t is None:
    st.error("⚠️ As medidas fornecidas geram uma quebra geométrica. Verifique os limites dos raios.")
else:
    area_tri = poly_tri.area
    peso_tri = area_tri * densidade
    
    area_t = poly_t.area
    peso_t = area_t * densidade
    
    reducao_perc = ((area_tri - area_t) / area_tri) * 100
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Peso Perfil Triangular", f"{peso_tri:.1f} g/m", f"Área: {area_tri:.3f} mm²")
    col_m2.metric("Peso Perfil T", f"{peso_t:.1f} g/m", f"Área: {area_t:.3f} mm²")
    col_m3.metric("Eficiência Alcançada", f"Redução de {reducao_perc:.2f}%", "Economia de Material", delta_color="inverse")

    # PREPARAÇÃO DA FOLHA A3/A4
    fig = plt.figure(figsize=(14, 16))
    fig.subplots_adjust(bottom=0.25, wspace=0.1)
    
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)
    
    offset = max(largura_total, altura) * 0.15 
    bbox_props = dict(facecolor='white', edgecolor='black', lw=1, pad=5)
    text_bbox = dict(facecolor='#f0f2f6', edgecolor='none', pad=1, alpha=0.9)
    
    def formatar_eixos(ax):
        ax.axis('off')
        ax.set_aspect('equal')
        ax.set_xlim(-largura_total/2 - offset*2.5, largura_total/2 + offset*2.5)
        ax.set_ylim(-offset*3, altura + offset*4)
        ax.plot([0, 0], [-offset*0.2, altura + offset*0.2], color='#ff00ff', lw=0.8, ls='-.')

    # ------------------------------------------
    # DESENHO 1: PERFIL TRIANGULAR
    # ------------------------------------------
    formatar_eixos(ax1)
    x1, y1 = poly_tri.exterior.xy
    ax1.plot(x1, y1, color='black', linewidth=1.5)
    ax1.fill(x1, y1, color='#f0f2f6', alpha=0.5)
    
    # Caixa Superior
    ax1.text(0, altura + offset*2.5, f"{peso_tri:.1f} g/m\nconsiderando densidade {densidade} g/cm³", 
             ha='center', va='center', fontsize=12, bbox=bbox_props)
    
    # Cruzes e Cotas Lineares
    xtr1, ytr1 = cent_tri
    ax1.plot([-xtr1, xtr1], [ytr1, ytr1], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax1.plot([0], [raio_base], marker='+', color='#ff00ff', markersize=8, ls='None')
    
    ax1.plot([-largura_total/2, -largura_total/2], [altura, altura + offset*0.5], color='green', lw=0.8, ls='-')
    ax1.plot([largura_total/2, largura_total/2], [altura, altura + offset*0.5], color='green', lw=0.8, ls='-')
    ax1.annotate('', xy=(-largura_total/2, altura + offset*0.4), xytext=(largura_total/2, altura + offset*0.4),
                 arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax1.text(0, altura + offset*0.5, f'{largura_total:.2f}', ha='center', va='bottom', fontsize=10, color='green')
    
    ax1.plot([xtr1 + 0.2, largura_total/2 + offset*0.6], [altura, altura], color='green', lw=0.8, ls='-')
    ax1.plot([0.2, largura_total/2 + offset*0.6], [0, 0], color='green', lw=0.8, ls='-')
    ax1.annotate('', xy=(largura_total/2 + offset*0.4, 0), xytext=(largura_total/2 + offset*0.4, altura),
                 arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax1.text(largura_total/2 + offset*0.6, altura/2, f'{altura:.2f}', ha='left', va='center', fontsize=10, color='green', rotation=90)
    
    # Raios e Ângulo Triangular
    ax1.annotate(f'R{raio_topo:.2f}', xy=(-xtr1, ytr1+raio_topo), xytext=(-largura_total/2 - offset, altura + offset*0.2),
                 arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    ax1.annotate(f'R{raio_base:.2f}', xy=(0, 0), xytext=(-offset*1.5, -offset*0.5),
                 arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    
    t1_x, t1_y = tang_tri['t1']
    t2_x, t2_y = tang_tri['t2']
    v_x = t2_x - t1_x
    v_y = t2_y - t1_y
    if v_x != 0:
        y_int = t1_y - t1_x * (v_y / v_x)
        y_vis = altura * 0.35
        r_arc = abs(y_vis - y_int)
        t_arc1, t_arc2 = (90 - ang_tri, 90) if y_int < y_vis else (270, 270 + ang_tri)
        
        arco = patches.Arc((0, y_int), r_arc*2, r_arc*2, theta1=t_arc1, theta2=t_arc2, color='green', lw=1)
        ax1.add_patch(arco)
        mid_ang = math.radians(t_arc1 + ang_tri/2)
        ax1.text(r_arc*0.7 * math.cos(mid_ang), y_int + r_arc*0.7 * math.sin(mid_ang), 
                 f'({ang_tri:.2f}°)', color='green', fontsize=10, ha='center', va='center', bbox=text_bbox)

    ax1.text(0, -offset*2, f"Área\n{area_tri:.3f} mm²", ha='center', va='center', fontsize=12)

    # ------------------------------------------
    # DESENHO 2: PERFIL T RAMPAS
    # ------------------------------------------
    formatar_eixos(ax2)
    x2, y2 = poly_t.exterior.xy
    ax2.plot(x2, y2, color='black', linewidth=1.5)
    ax2.fill(x2, y2, color='#f0f2f6', alpha=0.5)
    
    # Caixa Superior
    ax2.text(0, altura + offset*2.5, f"{peso_t:.1f} g/m\nconsiderando densidade {densidade} g/cm³", 
             ha='center', va='center', fontsize=12, bbox=bbox_props)
    
    xtr2, ytr2, xcc2, ycc2, pt2_x, pt2_y = cent_t
    ax2.plot([-xtr2, xtr2], [ytr2, ytr2], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax2.plot([-xcc2, xcc2], [ycc2, ycc2], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax2.plot([0], [raio_base], marker='+', color='#ff00ff', markersize=8, ls='None')
    
    ax2.plot([-largura_total/2, -largura_total/2], [altura, altura + offset*0.5], color='green', lw=0.8, ls='-')
    ax2.plot([largura_total/2, largura_total/2], [altura, altura + offset*0.5], color='green', lw=0.8, ls='-')
    ax2.annotate('', xy=(-largura_total/2, altura + offset*0.4), xytext=(largura_total/2, altura + offset*0.4),
                 arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax2.text(0, altura + offset*0.5, f'{largura_total:.2f}', ha='center', va='bottom', fontsize=10, color='green')
    
    ax2.plot([xtr2 + 0.2, largura_total/2 + offset*0.6], [altura, altura], color='green', lw=0.8, ls='-')
    ax2.plot([0.2, largura_total/2 + offset*0.6], [0, 0], color='green', lw=0.8, ls='-')
    ax2.annotate('', xy=(largura_total/2 + offset*0.4, 0), xytext=(largura_total/2 + offset*0.4, altura),
                 arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax2.text(largura_total/2 + offset*0.6, altura/2, f'{altura:.2f}', ha='left', va='center', fontsize=10, color='green', rotation=90)
    
    # Cota H_conn do T
    line_x_h = -largura_total/2 - offset*0.8
    ax2.plot([-largura_total/2 + 0.2, line_x_h], [altura, altura], color='green', lw=0.8, ls='-') 
    ax2.plot([-pt2_x - 0.2, line_x_h], [pt2_y, pt2_y], color='green', lw=0.8, ls='-')
    ax2.annotate('', xy=(line_x_h + 0.2, pt2_y), xytext=(line_x_h + 0.2, altura),
                 arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax2.text(line_x_h, (altura + pt2_y)/2, f'{h_conn:.2f}', ha='right', va='center', fontsize=10, color='green', rotation=90)
    
    # Raios e Ângulos T
    ax2.annotate(f'R{raio_topo:.2f}', xy=(-xtr2, ytr2+raio_topo), xytext=(-largura_total/2 - offset, altura + offset*0.2),
                 arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    ax2.annotate(f'R{raio_conn:.2f}', xy=(-xcc2+raio_conn, ycc2), xytext=(-largura_total/2 - offset, ycc2 - offset*0.5),
                 arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    ax2.annotate(f'R{raio_base:.2f}', xy=(0, 0), xytext=(-offset*1.5, -offset*0.5),
                 arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')

    t1_x, t1_y = tang_t['t1']
    v1_x, v1_y = tang_t['v1']
    t3_x, t3_y = tang_t['t3']
    v2_x, v2_y = tang_t['v2']
    
    if v1_x != 0:
        y_int_sup = t1_y - t1_x * (v1_y / v1_x)
        y_vis_sup = (t1_y + pt2_y) / 2 
        raio_arco_sup = abs(y_vis_sup - y_int_sup)
        arco_sup = patches.Arc((0, y_int_sup), raio_arco_sup*2, raio_arco_sup*2, 
                               theta1=90-angulo_sup, theta2=90, color='green', lw=1)
        ax2.add_patch(arco_sup)
        x_rampa_sup = t1_x + (y_vis_sup - t1_y) * (v1_x / v1_y)
        ax2.text(x_rampa_sup * 0.5, y_vis_sup, f'{angulo_sup:.0f}°', color='green', fontsize=10, ha='center', va='center', bbox=text_bbox)

    if v2_x != 0:
        y_int_inf = t3_y - t3_x * (v2_y / v2_x)
        t4_y_pt = tang_t['v2'][1] + t3_y 
        y_vis_inf = (t3_y + t4_y_pt) / 2 
        raio_arco_inf = abs(y_vis_inf - y_int_inf)
        t1_arc, t2_arc = (90 - ang_t, 90) if y_int_inf < y_vis_inf else (270, 270 + ang_t)
        arco_inf = patches.Arc((0, y_int_inf), raio_arco_inf*2, raio_arco_inf*2, 
                               theta1=t1_arc, theta2=t2_arc, color='green', lw=1)
        ax2.add_patch(arco_inf)
        x_rampa_inf = t3_x + (y_vis_inf - t3_y) * (v2_x / v2_y)
        ax2.text(x_rampa_inf * 0.5, y_vis_inf, f'({ang_t:.2f}°)', color='green', fontsize=10, ha='center', va='center', bbox=text_bbox)

    ax2.text(0, -offset*2, f"Área\n{area_t:.3f} mm²", ha='center', va='center', fontsize=12)

    # ------------------------------------------
    # INDICAÇÃO GLOBAL DE REDUÇÃO E CARIMBO
    # ------------------------------------------
    fig.text(0.5, 0.28, f"Redução de {reducao_perc:.2f}%", ha='center', va='center', fontsize=16, fontweight='bold')
    
    # Desenho do Carimbo Profissional em Eixo Dedicado
    ax_carimbo = fig.add_axes([0.1, 0.05, 0.8, 0.15])
    ax_carimbo.axis('off')
    
    # Moldura e Linhas da Tabela
    ax_carimbo.add_patch(patches.Rectangle((0, 0), 1, 1, fill=False, lw=1.5, transform=ax_carimbo.transAxes))
    ax_carimbo.plot([0, 1], [0.75, 0.75], color='black', lw=1, transform=ax_carimbo.transAxes)
    ax_carimbo.plot([0, 1], [0.50, 0.50], color='black', lw=1, transform=ax_carimbo.transAxes)
    ax_carimbo.plot([0, 1], [0.25, 0.25], color='black', lw=1, transform=ax_carimbo.transAxes)
    ax_carimbo.plot([0.3, 0.3], [0, 1], color='black', lw=1, transform=ax_carimbo.transAxes)
    ax_carimbo.plot([0.7, 0.7], [0, 1], color='black', lw=1, transform=ax_carimbo.transAxes)
    
    # Preenchimento de Dados do Carimbo
    ax_carimbo.text(0.15, 0.875, f"Comparativo {largura_total:.2f} x {altura:.2f}", ha='center', va='center', fontweight='bold', transform=ax_carimbo.transAxes)
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

    st.sidebar.divider()
    st.sidebar.download_button(
        label="📄 Exportar Folha Comparativa PDF",
        data=criar_pdf(fig),
        file_name=f"comparativo_reducao_{largura_total:.2f}x{altura:.2f}_{data_doc.strftime('%d%m%Y')}.pdf",
        mime="application/pdf"
    )
