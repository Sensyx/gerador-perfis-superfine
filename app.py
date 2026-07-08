import streamlit as st
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiPolygon
import math
import io

# 1. Configuração da Página (Design Industrial e Profissional)
st.set_page_config(page_title="Gerador de Perfis - Superfine Steel", layout="wide")
st.title("Documentação de Perfil: Triangular")

# 2. Formulário de Entrada (Campos digitáveis com botão de confirmação)
st.sidebar.header("Parâmetros do Perfil")

with st.sidebar.form("form_parametros"):
    largura = st.number_input("Largura da Base (mm)", value=10.60, step=0.10, format="%.2f")
    altura = st.number_input("Altura Total (mm)", value=5.30, step=0.10, format="%.2f")
    raio_topo = st.number_input("Raio do Topo (mm)", value=0.30, step=0.05, format="%.2f")
    raio_base = st.number_input("Raio da Base (mm)", value=0.45, step=0.05, format="%.2f")
    
    st.divider()
    densidade = st.number_input("Densidade (g/cm³)", value=8.50, step=0.10, format="%.2f")
    
    # Botão de confirmação
    submit_button = st.form_submit_button(label="Gerar Desenho Técnico")

# 3. Motor Geométrico (Cálculo de Tangência com Convex Hull)
def gerar_perfil_exato(w, h, r_top, r_base):
    # Trava de segurança para medidas impossíveis
    if r_base * 2 >= w or r_top + r_base >= h:
        return None
        
    # Cria os 3 círculos nos cantos respeitando as margens exatas da altura e largura
    canto_inf_esq = Point(-w/2 + r_base, r_base).buffer(r_base, resolution=64)
    canto_inf_dir = Point(w/2 - r_base, r_base).buffer(r_base, resolution=64)
    canto_sup = Point(0, h - r_top).buffer(r_top, resolution=64)
    
    # O "convex_hull" envelopa os 3 círculos criando linhas tangentes perfeitas entre eles
    perfil = MultiPolygon([canto_inf_esq, canto_inf_dir, canto_sup]).convex_hull
    return perfil

if submit_button or 'perfil_gerado' not in st.session_state:
    st.session_state.perfil_gerado = gerar_perfil_exato(largura, altura, raio_topo, raio_base)

perfil = st.session_state.perfil_gerado

# 4. Renderização e Cotagem (Estilo Desenho Técnico)
if perfil is None:
    st.error("⚠️ As medidas inseridas geram um conflito geométrico (ex: raios maiores que a peça). Verifique os valores.")
else:
    area_mm2 = perfil.area
    peso_por_metro = area_mm2 * densidade
    
    # Cálculo aproximado do ângulo lateral em relação à horizontal
    # (Usando o centro dos raios para calcular a inclinação)
    dx = (largura/2 - raio_base)
    dy = (altura - raio_topo - raio_base)
    angulo_rad = math.atan(dy / dx) if dx > 0 else 0
    angulo_graus = math.degrees(angulo_rad)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Desenho para Usinagem")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Desenha o polígono
        x, y = perfil.exterior.xy
        ax.plot(x, y, color='black', linewidth=1.5)
        ax.fill(x, y, color='#e5e7eb', alpha=0.5) # Cinza muito claro, padrão técnico
        
        # REMOVE O PLANO CARTESIANO (Eixos e Grid)
        ax.axis('off')
        ax.set_aspect('equal')
        
        # --- ADICIONA AS COTAS (Estilo Inventor) ---
        offset = max(largura, altura) * 0.1 # Distância dinâmica das cotas
        
        # Cota de Largura (Base)
        ax.annotate('', xy=(-largura/2, -offset), xytext=(largura/2, -offset),
                    arrowprops=dict(arrowstyle='<|-|>', color='black', lw=1))
        ax.text(0, -offset*1.5, f'{largura:.2f}', ha='center', va='center', fontsize=10)
        
        # Cota de Altura (Lateral Esquerda)
        ax.annotate('', xy=(-largura/2 - offset, 0), xytext=(-largura/2 - offset, altura),
                    arrowprops=dict(arrowstyle='<|-|>', color='black', lw=1))
        ax.text(-largura/2 - offset*1.5, altura/2, f'{altura:.2f}', ha='center', va='center', fontsize=10, rotation=90)
        
        # Indicação do Raio do Topo
        ax.annotate(f'R{raio_topo:.2f}', xy=(0, altura), xytext=(largura*0.2, altura + offset),
                    arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=.2", color='black', lw=1), fontsize=10)
        
        # Indicação do Raio da Base (Direita)
        ax.annotate(f'R{raio_base:.2f}', xy=(largura/2, 0), xytext=(largura/2 + offset, -offset/2),
                    arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=-.2", color='black', lw=1), fontsize=10)
        
        # Indicação do Ângulo
        ax.text(largura/4, altura/2, f'{angulo_graus:.2f}°', ha='left', va='bottom', fontsize=9, color='#333333')

        st.pyplot(fig)

    with col2:
        st.subheader("Resultados")
        # Formatação idêntica ao PDF de referência
        st.metric(label="Área", value=f"{area_mm2:.3f} mm²")
        st.metric(label="Peso", value=f"{peso_por_metro:.1f} g/m")
        
    # 5. Exportação para PDF
    def criar_pdf(figura):
        buf = io.BytesIO()
        figura.savefig(buf, format="pdf", bbox_inches="tight")
        buf.seek(0)
        return buf

    st.sidebar.divider()
    st.sidebar.download_button(
        label="📄 Exportar PDF",
        data=criar_pdf(fig),
        file_name=f"perfil_triangular_{largura:.2f}x{altura:.2f}.pdf",
        mime="application/pdf"
    )
