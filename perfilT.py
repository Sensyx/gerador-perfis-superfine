import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon
import math
import io

st.set_page_config(page_title="Gerador de Perfis - Superfine Steel", layout="wide")
st.title("Documentação de Perfil: Tipo T (Rampas Inclinadas)")

st.sidebar.header("Parâmetros do Perfil")

with st.sidebar.form("form_parametros"):
    largura_total = st.number_input("Largura Total do Topo (mm)", value=4.20, step=0.10, format="%.2f")
    altura = st.number_input("Altura Total (mm)", value=10.60, step=0.10, format="%.2f")
    
    st.divider()
    raio_topo = st.number_input("Raio do Topo (mm)", value=0.30, step=0.05, format="%.2f")
    raio_base = st.number_input("Raio da Base (mm)", value=0.45, step=0.05, format="%.2f")
    raio_conn = st.number_input("Raio de Conexão (mm)", value=0.50, step=0.05, format="%.2f")
    
    # Atualizado para indicar que agora parte do Topo
    h_conn = st.number_input("Altura de Tangência (mm)", value=1.58, step=0.05, format="%.2f", help="Medido do Topo da peça até o ponto de tangência do raio de conexão")
    
    st.divider()
    angulo_sup = st.number_input("Ângulo Rampa Superior (°)", value=39.0, step=0.5, format="%.1f")
    densidade = st.number_input("Densidade (g/cm³)", value=8.50, step=0.10, format="%.2f")
    
    submit_button = st.form_submit_button(label="Gerar Desenho Técnico")

def gerar_perfil_t_rampas(w_total, h, r_top, r_base, r_conn, h_conn_val, ang_sup_deg):
    try:
        alpha = math.radians(ang_sup_deg)
        
        # 1. Topo 
        x_tr = (w_total / 2) - r_top
        y_tr = h - r_top
        
        n1_x = math.cos(alpha)
        n1_y = -math.sin(alpha)
        t1_x = x_tr + r_top * n1_x
        t1_y = y_tr + r_top * n1_y
        
        v1_x = -math.sin(alpha)
        v1_y = -math.cos(alpha)
        
        # 2. Centro do Raio de Conexão (AGORA MEDIDO A PARTIR DE 'h' - O Topo Físico)
        t2_y = h - h_conn_val
        k = (t2_y - t1_y) / v1_y if v1_y != 0 else 0
        t2_x = t1_x + k * v1_x
        
        x_cc = t2_x + r_conn * n1_x
        y_cc = t2_y + r_conn * n1_y
        
        # 3. Tangente Interna (Rampa Inferior)
        dy = y_cc - r_base
        dx = x_cc
        dist = math.hypot(dx, dy)
        
        gamma = math.atan2(dy, dx)
        delta = math.acos((r_base + r_conn) / dist)
        
        phi = gamma - delta 
        n2_x = math.cos(phi)
        n2_y = math.sin(phi)
        
        ang_inf_deg = -math.degrees(phi)
        
        # 4. Gerador de Arcos
        def arc(cx, cy, r, a1, a2, cw=True, steps=100):
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
        
        # 5. Montagem do Polígono
        right_half = [(0, h), (x_tr, h)] + arc_top + arc_conn + arc_base + [(0, 0)]
        left_half = [(-x, y) for x, y in reversed(right_half)]
        poly_points = right_half + left_half[1:-1]
        
        t3_x_pt = x_cc - r_conn * n2_x
        t3_y_pt = y_cc - r_conn * n2_y
        t4_x_pt = r_base * n2_x
        t4_y_pt = r_base + r_base * n2_y
        
        tangentes = {
            't1': (t1_x, t1_y),
            'v1': (t2_x - t1_x, t2_y - t1_y),
            't3': (t3_x_pt, t3_y_pt),
            'v2': (t4_x_pt - t3_x_pt, t4_y_pt - t3_y_pt),
            'a1_conn': a1_conn,
            'a2_conn': a2_conn
        }
        
        return Polygon(poly_points), ang_inf_deg, (x_tr, y_tr, x_cc, y_cc, t2_x, t2_y), tangentes
    
    except Exception as e:
        return None, None, None, None

if submit_button or 'perfil_t_calc_v8' not in st.session_state:
    st.session_state.perfil_t_calc_v8 = gerar_perfil_t_rampas(largura_total, altura, raio_topo, raio_base, raio_conn, h_conn, angulo_sup)

perfil, angulo_inf_calculado, centros, tangentes = st.session_state.perfil_t_calc_v8

if perfil is None:
    st.error("⚠️ As medidas fornecidas não formam uma geometria tangencial válida. Verifique os raios e ângulos.")
else:
    area_mm2 = perfil.area
    peso_por_metro = area_mm2 * densidade
    x_tr, y_tr, x_cc, y_cc, t2_x, t2_y = centros

    col1, col2 = st.columns([2, 1])

    with col1:
        fig, ax = plt.subplots(figsize=(9, 12))
        
        x, y = perfil.exterior.xy
        ax.plot(x, y, color='black', linewidth=1.5)
        ax.fill(x, y, color='#f0f2f6', alpha=0.5)
        
        ax.axis('off')
        ax.set_aspect('equal')
        
        offset = max(largura_total, altura) * 0.15 
        ax.set_xlim(-largura_total/2 - offset*2.5, largura_total/2 + offset*2.5)
        ax.set_ylim(-offset*1.5, altura + offset*1.5)
        
        # Linha de Centro (Dentro da margem da peça)
        ax.plot([0, 0], [-offset*0.2, altura + offset*0.2], color='#ff00ff', lw=0.8, ls='-.')
        
        # Cruzes dos Centros
        ax.plot([-x_tr, x_tr], [y_tr, y_tr], marker='+', color='#ff00ff', markersize=8, ls='None')
        ax.plot([-x_cc, x_cc], [y_cc, y_cc], marker='+', color='#ff00ff', markersize=8, ls='None')
        ax.plot([0], [raio_base], marker='+', color='#ff00ff', markersize=8, ls='None')

        # --- COTAS LINEARES ---
        # Largura Total
        ax.plot([-largura_total/2, -largura_total/2], [altura, altura + offset*0.5], color='green', lw=0.8, ls='-')
        ax.plot([largura_total/2, largura_total/2], [altura, altura + offset*0.5], color='green', lw=0.8, ls='-')
        ax.annotate('', xy=(-largura_total/2, altura + offset*0.4), xytext=(largura_total/2, altura + offset*0.4),
                    arrowprops=dict(arrowstyle='<|-|>', color='green', shrinkA=0, shrinkB=0, lw=1))
        ax.text(0, altura + offset*0.5, f'{largura_total:.2f}', ha='center', va='bottom', fontsize=10, color='green')

        # Altura Total
        ax.plot([x_tr + 0.2, largura_total/2 + offset*0.6], [altura, altura], color='green', lw=0.8, ls='-')
        ax.plot([0.2, largura_total/2 + offset*0.6], [0, 0], color='green', lw=0.8, ls='-')
        ax.annotate('', xy=(largura_total/2 + offset*0.4, 0), xytext=(largura_total/2 + offset*0.4, altura),
                    arrowprops=dict(arrowstyle='<|-|>', color='green', shrinkA=0, shrinkB=0, lw=1))
        ax.text(largura_total/2 + offset*0.6, altura/2, f'{altura:.2f}', ha='left', va='center', fontsize=10, color='green', rotation=90)

        # Cota de h_conn (AGORA PUXANDO DA ARESTA DO TOPO 'h')
        line_x_h = -largura_total/2 - offset*0.8 # Afastado ligeiramente para não bater na cota de Raio
        ax.plot([-largura_total/2 + 0.2, line_x_h], [altura, altura], color='green', lw=0.8, ls='-') # Puxa do topo
        ax.plot([-t2_x - 0.2, line_x_h], [t2_y, t2_y], color='green', lw=0.8, ls='-')
        ax.annotate('', xy=(line_x_h + 0.2, t2_y), xytext=(line_x_h + 0.2, altura),
                    arrowprops=dict(arrowstyle='<|-|>', color='green', shrinkA=0, shrinkB=0, lw=1))
        ax.text(line_x_h, (altura + t2_y)/2, f'{h_conn_val:.2f}', ha='right', va='center', fontsize=10, color='green', rotation=90)

        # --- MOTOR DE CÁLCULO PERIMETRAL PARA SETAS DE RAIO ---
        def get_perimeter_point(cx, cy, r, tx, ty, concave=False):
            dx, dy = cx - tx, cy - ty
            d = math.hypot(dx, dy)
            if d == 0: return cx, cy
            ux, uy = dx/d, dy/d
            if concave: return cx + r * ux, cy + r * uy
            else: return cx - r * ux, cy - r * uy

        tx_top, ty_top = -largura_total/2 - offset*0.6, y_tr + offset*0.4
        px_top, py_top = get_perimeter_point(-x_tr, y_tr, raio_topo, tx_top, ty_top, False)

        tx_conn, ty_conn = -largura_total/2 - offset*0.7, y_cc - offset*0.4
        px_conn, py_conn = get_perimeter_point(-x_cc, y_cc, raio_conn, tx_conn, ty_conn, True)

        tx_base, ty_base = -offset*1.5, -offset*0.5
        px_base, py_base = get_perimeter_point(0, raio_base, raio_base, tx_base, ty_base, False)

        ax.annotate(f'R{raio_topo:.2f}', xy=(px_top, py_top), xytext=(tx_top, ty_top),
                    arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
        ax.annotate(f'R{raio_conn:.2f}', xy=(px_conn, py_conn), xytext=(tx_conn, ty_conn),
                    arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
        ax.annotate(f'R{raio_base:.2f}', xy=(px_base, py_base), xytext=(tx_base, ty_base),
                    arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')

        # --- COTAS DE ÂNGULO (Centralizadas horizontal e verticalmente na rampa) ---
        t1_x, t1_y = tangentes['t1']
        v1_x, v1_y = tangentes['v1']
        t3_x, t3_y = tangentes['t3']
        v2_x, v2_y = tangentes['v2']
        
        text_bbox = dict(facecolor='#f0f2f6', edgecolor='none', pad=1, alpha=0.9)
        
        # Rampa Superior (39°)
        if v1_x != 0:
            y_int_sup = t1_y - t1_x * (v1_y / v1_x)
            y_vis_sup = (t1_y + t2_y) / 2 # Ponto médio exato da rampa visível
            raio_arco_sup = abs(y_vis_sup - y_int_sup)
            
            arco_sup = patches.Arc((0, y_int_sup), raio_arco_sup*2, raio_arco_sup*2, 
                                   theta1=90-angulo_sup, theta2=90, color='green', lw=1)
            ax.add_patch(arco_sup)
            
            # Centraliza o texto na metade horizontal da rampa 
            x_rampa_sup = t1_x + (y_vis_sup - t1_y) * (v1_x / v1_y)
            ax.text(x_rampa_sup * 0.5, y_vis_sup, f'{angulo_sup:.0f}°', color='green', 
                    fontsize=10, ha='center', va='center', bbox=text_bbox)

        # Rampa Inferior (Referência)
        if v2_x != 0:
            y_int_inf = t3_y - t3_x * (v2_y / v2_x)
            t4_y_pt = tangentes['v2'][1] + t3_y # Coordenada Y do fim da rampa
            y_vis_inf = (t3_y + t4_y_pt) / 2 # Ponto médio exato da rampa visível
            raio_arco_inf = abs(y_vis_inf - y_int_inf)
            
            # Define o arco independente de onde a intersecção aconteça
            t1_arc, t2_arc = (90 - angulo_inf_calculado, 90) if y_int_inf < y_vis_inf else (270, 270 + angulo_inf_calculado)
            
            arco_inf = patches.Arc((0, y_int_inf), raio_arco_inf*2, raio_arco_inf*2, 
                                   theta1=t1_arc, theta2=t2_arc, color='green', lw=1)
            ax.add_patch(arco_inf)
            
            # Centraliza o texto na metade horizontal da rampa 
            x_rampa_inf = t3_x + (y_vis_inf - t3_y) * (v2_x / v2_y)
            ax.text(x_rampa_inf * 0.5, y_vis_inf, f'({angulo_inf_calculado:.2f}°)', color='green', 
                    fontsize=10, ha='center', va='center', bbox=text_bbox)

        # Quadro Carimbo
        texto_carimbo = (
            f"Superfine Steel Aços Inoxidáveis\n"
            f"----------------------------------------\n"
            f"Perfil T c/ Rampas\n"
            f"Área: {area_mm2:.3f} mm²\n"
            f"Peso: {peso_por_metro:.1f} g/m\n"
            f"Densidade: {densidade:.2f} g/cm³\n"
            f"----------------------------------------\n"
            f"Desenhado por: Felipe\n"
            f"Aprovado por: Paulo"
        )
        ax.text(largura_total/2 + offset*1.0, altura, texto_carimbo, ha='left', va='top', 
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.8'), fontsize=8, family='monospace')

        st.pyplot(fig)

    with col2:
        st.subheader("Resultados Físicos")
        st.metric(label="Área", value=f"{area_mm2:.3f} mm²")
        st.metric(label="Peso Linear", value=f"{peso_por_metro:.1f} g/m")
        st.metric(label="Ângulo Inferior (Referência)", value=f"{angulo_inf_calculado:.2f}°")

    def criar_pdf(figura):
        buf = io.BytesIO()
        figura.savefig(buf, format="pdf", bbox_inches="tight", pad_inches=0.2)
        buf.seek(0)
        return buf

    st.sidebar.divider()
    st.sidebar.download_button(
        label="📄 Exportar PDF",
        data=criar_pdf(fig),
        file_name=f"perfil_T_rampas_{largura_total:.2f}x{altura:.2f}.pdf",
        mime="application/pdf"
    )
