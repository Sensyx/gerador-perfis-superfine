import streamlit as st
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely import buffer

# 1. Configuração da Interface (Estética minimalista e profissional)
st.set_page_config(page_title="Gerador de Perfis - Superfine Steel", layout="wide")
st.title("Gerador Paramétrico de Perfis Laminados")

# 2. Painel Lateral para Inputs do Usuário (Sliders)
st.sidebar.header("Parâmetros do Perfil")
tipo_perfil = st.sidebar.selectbox("Tipo de Perfil", ["Retangular", "Triangular", "Tipo T", "Chato"])

# Exemplo de parâmetros para um perfil retangular com raios
largura = st.sidebar.slider("Largura (mm)", 1.0, 50.0, 10.60, step=0.1)
altura = st.sidebar.slider("Altura (mm)", 1.0, 50.0, 5.30, step=0.1)
raio_canto = st.sidebar.slider("Raio dos Cantos (mm)", 0.0, 5.0, 0.45, step=0.05)
densidade = st.sidebar.number_input("Densidade (g/cm³)", value=8.5, format="%.2f")

# 3. Motor Geométrico (Exemplo simplificado para cantos arredondados)
def gerar_perfil_retangular(l, h, r):
    # Cria o retângulo base
    base = Polygon([(0, 0), (l, 0), (l, h), (0, h)])
    
    # Aplica o raio (buffer) - a lógica real pode exigir precisão tangencial usando subtract
    if r > 0:
         base = base.buffer(-r).buffer(r)
    return base

perfil = gerar_perfil_retangular(largura, altura, raio_canto)

# 4. Cálculos
area_mm2 = perfil.area
peso_por_metro = area_mm2 * densidade

# 5. Renderização na Tela Principal
fig, ax = plt.subplots(figsize=(8, 4))
x, y = perfil.exterior.xy
ax.plot(x, y, color='#2c3e50', linewidth=2)
ax.fill(x, y, color='#95a5a6', alpha=0.5)
ax.set_aspect('equal')
ax.grid(True, linestyle='--', alpha=0.6)
st.pyplot(fig)

# ==========================================
# NOVA FUNÇÃO: EXPORTAÇÃO PARA PDF
# ==========================================

def criar_pdf_simples(figura):
    """
    Salva o gráfico do matplotlib diretamente como PDF em um buffer de memória.
    """
    buf = io.BytesIO()
    # bbox_inches="tight" remove bordas brancas excessivas
    figura.savefig(buf, format="pdf", bbox_inches="tight")
    buf.seek(0)
    return buf

# Gera o arquivo em memória
pdf_buffer = criar_pdf_simples(fig)

# Adiciona o botão na barra lateral (ou na tela principal)
st.sidebar.divider()
st.sidebar.subheader("Documentação")

st.sidebar.download_button(
    label="📄 Baixar Desenho em PDF",
    data=pdf_buffer,
    file_name=f"perfil_{tipo_perfil.lower()}_{largura}x{altura}.pdf",
    mime="application/pdf",
    help="Exporta o desenho atual em formato PDF vetorial."
)
