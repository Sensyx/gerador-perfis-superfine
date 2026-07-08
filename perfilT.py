import streamlit as st
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import math
import io

st.set_page_config(page_title="Gerador de Perfis - Superfine Steel", layout="wide")
st.title("Documentação de Perfil: Tipo T (Rampas Inclinadas)")

st.sidebar.header("Parâmetros do Perfil")

with st.sidebar.form("form_parametros"):
    # A cota de 5.30 no desenho vai exatamente nos centros dos raios de 0.30
    largura_centros = st.number_input("Largura entre Centros do Topo (mm)", value=5.30, step=0.10, format="%.2f")
    altura = st.number_input("Altura Total (mm)", value=10.60, step=0.10, format="%.2f")
    
    st.divider()
    raio_topo = st.number_input("Raio do Topo (mm)", value=0.30, step=0.05, format="%.2f")
    raio_base = st.number_input("Raio da Base (mm)", value=0.45, step=0.05, format="%.2f")
    raio_conn = st.number_input("Raio de Conexão (mm)", value=0.50, step=0.05, format="%.2f")
    h_conn = st.number_input("Altura do Raio de Conexão (mm)", value=1.71, step=0.05, format="%.2f")
    
    st.divider()
    angulo_sup = st.number_input("Ângulo Rampa Superior (°)", value=39.0, step=0.5, format="%.1f")
    densidade = st.number_input("Densidade (g/cm³)", value=8.50, step=0.10, format="%.2f")
    
    submit_button = st.form_submit_button(label="Gerar Desenho Técnico")

def gerar_perfil_t_rampas(w_centros, h, r_top, r_base, r_conn, h_conn, ang_sup_deg):
    try:
        alpha = math.radians(ang_sup_deg)
        
        # 1. Topo (Centros e Tangentes)
        x_tr = w_centros / 2
        y_tr = h - r_top
        
        # Vetor normal da rampa superior (apontando para fora/direita)
        n1_x = math.cos(alpha)
        n1_y = -math.sin(alpha)
        
        # Ponto de tangência no raio do topo
        t1_x = x_tr + r_top * n1_x
        t1_y = y_tr + r_top * n1_y
        
        # Vetor direção da rampa (apontando para baixo/esquerda)
        v1_x = -math.sin(alpha)
        v1_y = -math.cos(alpha)
        
        # 2. Centro do Raio de Conexão (R0.50)
        y_cc = h - h_conn
        # Distância tangencial até o centro do raio de conexão
        t = (y_cc - t1_y - r_conn * n1_y) / v1_y
        x_cc = t1_x + t * v1_x + r_conn * n1_x
        
        # Ponto de tangência superior no raio de conexão
        t2_x = x_cc - r_conn * n1_x
        t2_y = y_cc - r_conn * n1_y
        
        # 3. Tangente Interna (Rampa Inferior)
        dy = y_cc - r_base
        dx = x_cc
        dist = math.hypot(dx, dy)
        
        gamma = math.atan2(dy, dx)
        delta = math.acos((r_base + r_conn) / dist)
        
        # Ângulo normal da rampa inferior
        phi = gamma - delta 
        n2_x = math.cos(phi)
        n2_y = math.sin(phi)
        
        # Ponto de tangência inferior no raio de conexão
        t3_x = x_cc - r_conn * n2_x
        t3_y = y_cc - r_conn * n2_y
        
        # Ponto de tangência na base
        t4_x = 0 + r_base * n2_x
        t4_y = r_base + r_base * n2_y
        
        # O ângulo gerado matematicamente (Resultado)
        ang_inf_deg = math.degrees(-phi)
        
        # 4. Gerador de Arcos
        def arc(cx, cy, r, a1, a2, cw=True, steps=20):
            pts = []
            if cw:
                while a2 > a1: a2 -= 2*math.pi
            else:
                while a2 < a1: a2 += 2*math.pi
            for i in range(steps + 1):
                ang = a1 + (a2 - a1) * (i / steps)
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
            return pts

        # Definição dos ângulos dos arcos
        a1_top = math.pi / 2
        a2_top = math.atan2(n1_y, n1_x)
        arc_top = arc(x_tr, y_tr, r_top, a1_top, a2_top, cw=True)
        
        a1_conn = math.atan2(-n1_y, -n1_x)
        a2_conn = math.atan2(-n2_y, -n2_x)
        arc_conn = arc(x_cc, y_cc, r_conn, a1_conn, a2_conn, cw=False) # Côncavo = Anti-horário
        
        a1_base = math.atan2(n2_y, n2_x)
        a2_base = -math.pi / 2
        arc_base = arc(0, r_base, r_base, a1_base, a2_base, cw=True)
        
        # 5. Montagem do Polígono
        right_half = [(0, h), (x_tr, h)] + arc_top + arc_conn + arc_base + [(0, 0)]
        left_half = [(-x, y) for x, y in reversed(right_half)]
        
        # Remove pontos duplicados no eixo Y (0,0 e 0,h)
        poly_points = right_half + left_half[1:-1]
        
        return Polygon(poly_points), ang_inf_deg, (x_tr, y_tr, x_cc, y_cc)
    
    except Exception as e:
        return None, None, None

if submit_button or 'perfil_t_calc' not in st.session_state:
    st.session_state.perfil_t_calc = gerar_perfil_t_rampas(largura_centros, altura, raio_topo, raio_base, raio_conn, h_conn, angulo_sup)

perfil, angulo_inf_calculado, centros = st.session_state.perfil_t_calc

if perfil is None:
    st.error("⚠️ As medidas fornecidas não formam uma geometria tangencial válida. Verifique os raios e ângulos.")
else:
    area_mm2 = perfil.area
    peso_por_metro = area_mm2 * densidade
    x_tr, y_tr, x_cc, y_cc = centros

    col1, col2 = st.columns([2, 1])

    with col1:
        fig, ax = plt.subplots(figsize=(8, 12))
        
        x, y = perfil.exterior.xy
        ax.plot(x, y, color='black', linewidth=1.5)
        ax.fill(x, y, color='#f0f2f6', alpha=0.5)
        
        ax.axis('off')
        ax.set_aspect('equal')
        
        offset = max(largura_centros, altura) * 0.15 
        ax.set_xlim(-largura_centros/2 - offset*3, largura_centros/2 + offset*4)
        ax.set_ylim(-offset, altura + offset*1.5)
        
        # Linha de Centro (Estilo CAD rosa pontilhado)
        ax.plot([0, 0], [-offset*0.5, altura + offset*0.8], color='#ff00ff', lw=0.8, ls='-.')
        
        # Cruzes dos Centros (Rosa)
        ax.plot([-x_tr, x_tr], [y_tr, y_tr], marker='+', color='#ff00ff', markersize=8, ls='None')
        ax.plot([-x_cc, x_cc], [y_cc, y_cc], marker='+', color='#ff00ff', markersize=8, ls='None')
        ax.plot([0], [raio_base], marker='+', color='#ff00ff', markersize=8, ls='None')

        # --- COTAS ---
        # Largura 5.30
        ax.plot([-x_tr, -x_tr], [y_tr, altura + offset*0.6], color='green', lw=0.8, ls='-')
        ax.plot([x_tr, x_tr], [y_tr, altura + offset*0.6], color='green', lw=0.8, ls='-')
        ax.annotate('', xy=(-x_tr, altura + offset*0.4), xytext=(x_tr, altura + offset*0.4),
                    arrowprops=dict(arrowstyle='<|-|>', color='green', shrinkA=0, shrinkB=0, lw=1))
        ax.text(0, altura + offset*0.5, f'{largura_centros:.2f}', ha='center', va='bottom', fontsize=10, color='green')

        # Altura 10.60
        ax.plot([x_tr + 0.5, largura_centros/2 + offset*1.5], [altura, altura], color='green', lw=0.8, ls='-')
        ax.plot([0.5, largura_centros/2 + offset*1.5], [0, 0], color='green', lw=0.8, ls='-')
        ax.annotate('', xy=(largura_centros/2 + offset*1.2, 0), xytext=(largura_centros/2 + offset*1.2, altura),
                    arrowprops=dict(arrowstyle='<|-|>', color='green', shrinkA=0, shrinkB=0, lw=1))
        ax.text(largura_centros/2 + offset*1.4, altura/2, f'{altura:.2f}', ha='left', va='center', fontsize=10, color='green', rotation=90)

        # Altura Conexão 1.71
        ax.plot([-x_tr - 0.5, -x_tr - offset*1.5], [altura, altura], color='green', lw=0.8, ls='-')
        ax.plot([-x_cc - 0.5, -x_tr - offset*1.5], [y_cc, y_cc], color='green', lw=0.8, ls='-')
        ax.annotate('', xy=(-x_tr - offset*1.2, y_cc), xytext=(-x_tr - offset*1.2, altura),
                    arrowprops=dict(arrowstyle='<|-|>', color='green', shrinkA=0, shrinkB=0, lw=1))
        ax.text(-x_tr - offset*1.4, (altura + y_cc)/2, f'{h_conn:.2f}', ha='right', va='center', fontsize=10, color='green', rotation=90)

        # Raios (R0.30, R0.50, R0.45)
        ax.annotate(f'R{raio_topo:.2f}', xy=(-x_tr, y_tr+raio_topo), xytext=(-x_tr - offset, altura + offset*0.2),
                    arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
        ax.annotate(f'R{raio_conn:.2f}', xy=(-x_cc+raio_conn, y_cc), xytext=(-x_cc - offset, y_cc - offset*0.5),
                    arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
        ax.annotate(f'R{raio_base:.2f}', xy=(0, 0), xytext=(-offset*1.5, -offset*0.5),
                    arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')

        # Ângulos
        ax.text(offset*0.8, y_cc, f'{angulo_sup:.0f}°', color='green', fontsize=10)
        ax.text(-offset*1.5, altura/3, f'({angulo_inf_calculado:.2f}°)', color='green', fontsize=10)

        # Carimbo
        texto_carimbo = (
            f"Superfine Steel Aços Inoxidáveis\n"
            f"----------------------------------------\n"
            f"Perfil T c/ Rampas\n"
            f"Área: {area_mm2:.3f} mm²\n"
            f"Peso: {peso_por_metro:.1f} g/m\n"
            f"Densidade: {densidade:.2f} g/cm³\n"
            f"----------------------------------------\n"
            f"Desenhado por: Felipe"
        )
        ax.text(largura_centros/2 + offset*1.8, altura, texto_carimbo, ha='left', va='top', 
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.8'), fontsize=8, family='monospace')

        st.pyplot(fig)

    with col2:
        st.subheader("Resultados")
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
        file_name=f"perfil_T_rampas_{largura_centros:.2f}x{altura:.2f}.pdf",
        mime="application/pdf"
    )
