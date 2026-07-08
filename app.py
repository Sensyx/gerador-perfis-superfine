import streamlit as st
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiPolygon
import math
import io

st.set_page_config(page_title="Gerador de Perfis - Superfine Steel", layout="wide")
st.title("Documentação de Perfil: Triangular")

st.sidebar.header("Parâmetros do Perfil")

with st.sidebar.form("form_parametros"):
    largura = st.number_input("Largura da Base (mm)", value=5.30, step=0.10, format="%.2f")
    altura = st.number_input("Altura Total (mm)", value=10.60, step=0.10, format="%.2f")
    raio_topo = st.number_input("Raio do Topo (mm)", value=0.45, step=0.05, format="%.2f")
    raio_base = st.number_input("Raio da Base (mm)", value=0.30, step=0.05, format="%.2f")
    
    st.divider()
    densidade = st.number_input("Densidade (g/cm³)", value=8.50, step=0.10, format="%.2f")
    
    submit_button = st.form_submit_button(label="Gerar Desenho Técnico")

def gerar_perfil_exato(w, h, r_top, r_base):
    if r_base * 2 >= w or r_top + r_base >= h:
        return None
        
    canto_inf_esq = Point(-w/2 + r_base, r_base).buffer(r_base, resolution=64)
    canto_inf_dir = Point(w/2 - r_base, r_base).buffer(r_base, resolution=64)
    canto_sup = Point(0, h - r_top).buffer(r_top, resolution=64)
    
    return MultiPolygon([canto_inf_esq, canto_inf_dir, canto_sup]).convex_hull

if submit_button or 'perfil_gerado' not in st.session_state:
    st.session_state.perfil_gerado = gerar_perfil_exato(largura, altura, raio_topo, raio_base)

perfil = st.session_state.perfil_gerado

if perfil is None:
    st.error("⚠️ As medidas inseridas geram um conflito geométrico. Verifique os valores.")
else:
    area_mm2 = perfil.area
    peso_por_metro = area_mm2 * densidade
    
    # --- CÁLCULO EXATO DO ÂNGULO DA RAMPA LATERAL (12,57°) ---
    dx = (largura / 2) - raio_base
    dy = altura - raio_topo - raio_base
    distancia_centros = math.hypot(dx, dy)
    
    if distancia_centros > 0:
        ang_centros = math.degrees(math.atan2(dx, dy))
        seno_diferenca = (raio_topo - raio_base) / distancia_centros
        seno_diferenca = max(-1.0, min(1.0, seno_diferenca)) # Trava de segurança
        ang_tangente = math.degrees(math.asin(seno_diferenca))
        
        # O ângulo final em relação à vertical
        angulo_graus = ang_centros - ang_tangente
    else:
        angulo_graus = 0

    col1, col2 = st.columns([2, 1])

    with col1:
        fig, ax = plt.subplots(figsize=(8, 10))
        
        x, y = perfil.exterior.xy
        ax.plot(x, y, color='black', linewidth=1.5)
        ax.fill(x, y, color='#f0f2f6', alpha=0.5) 
        
        ax.axis('off')
        ax.set_aspect('equal')
        
        offset = max(largura, altura) * 0.15 
        
        # --- FORÇA OS LIMITES PARA NÃO CORTAR AS COTAS ---
        ax.set_xlim(-largura/2 - offset*2, largura/2 + offset*4)
        ax.set_ylim(-offset*2, altura + offset*2)
        
        # --- LINHAS DE CHAMADA E COTAS ---
        # Largura
        ax.plot([-largura/2, -largura/2], [-0.2, -offset*1.1], color='gray', lw=0.8, ls=':')
        ax.plot([largura/2, largura/2], [-0.2, -offset*1.1], color='gray', lw=0.8, ls=':')
        ax.annotate('', xy=(-largura/2, -offset), xytext=(largura/2, -offset),
                    arrowprops=dict(arrowstyle='<|-|>', color='black', shrinkA=0, shrinkB=0, lw=1))
        ax.text(0, -offset*1.3, f'{largura:.2f}', ha='center', va='top', fontsize=10)
        
        # Altura
        ax.plot([-largura/2 - 0.2, -largura/2 - offset*1.1], [0, 0], color='gray', lw=0.8, ls=':')
        ax.plot([-0.2, -largura/2 - offset*1.1], [altura, altura], color='gray', lw=0.8, ls=':')
        ax.annotate('', xy=(-largura/2 - offset, 0), xytext=(-largura/2 - offset, altura),
                    arrowprops=dict(arrowstyle='<|-|>', color='black', shrinkA=0, shrinkB=0, lw=1))
        ax.text(-largura/2 - offset*1.3, altura/2, f'{altura:.2f}', ha='right', va='center', fontsize=10, rotation=90)
        
        # Raios
        ax.annotate(f'R{raio_topo:.2f}', xy=(0, altura), xytext=(largura*0.5, altura + offset*0.5),
                    arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=.2", color='black', shrinkB=0, lw=1), fontsize=10)
        
        ax.annotate(f'R{raio_base:.2f}', xy=(largura/2, 0), xytext=(largura/2 + offset*0.8, -offset*0.5),
                    arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=-.2", color='black', shrinkB=0, lw=1), fontsize=10)
        
        # Ângulo e Linha de Centro
        ax.plot([0, 0], [-offset*0.5, altura + offset*0.5], color='gray', lw=0.8, ls='-.') # Linha de simetria
        ax.text(largura/4, altura/2, f'({angulo_graus:.2f}°)', ha='left', va='center', fontsize=10)

        # --- QUADRO TÉCNICO INSERIDO NO PDF ---
        texto_carimbo = (
            f"Superfine Steel Aços Inoxidáveis\n"
            f"----------------------------------------\n"
            f"Perfil Triangular\n"
            f"Área: {area_mm2:.3f} mm²\n"
            f"Peso: {peso_por_metro:.1f} g/m\n"
            f"Densidade: {densidade:.2f} g/cm³\n"
            f"----------------------------------------\n"
            f"Desenhado por: Felipe\n"
            f"Aprovado por: Paulo"
        )
        # Posiciona o texto na lateral direita superior
        ax.text(largura/2 + offset*0.8, altura, texto_carimbo, ha='left', va='top', 
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='square,pad=0.8'), fontsize=8, family='monospace')

        st.pyplot(fig)

    with col2:
        st.subheader("Resultados")
        st.metric(label="Área", value=f"{area_mm2:.3f} mm²")
        st.metric(label="Peso Linear", value=f"{peso_por_metro:.1f} g/m")
        
    def criar_pdf(figura):
        buf = io.BytesIO()
        figura.savefig(buf, format="pdf", bbox_inches="tight", pad_inches=0.2)
        buf.seek(0)
        return buf

    st.sidebar.divider()
    st.sidebar.download_button(
        label="📄 Exportar PDF",
        data=criar_pdf(fig),
        file_name=f"perfil_triangular_{largura:.2f}x{altura:.2f}.pdf",
        mime="application/pdf"
    )
