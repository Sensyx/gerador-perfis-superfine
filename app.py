import streamlit as st
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
import io

# 1. Configuração Visual da Página (Design minimalista e industrial)
st.set_page_config(page_title="Gerador de Perfis - Superfine Steel", layout="wide")
st.title("Parâmetros de Laminação: Perfil Triangular")

# 2. Interface de Controles (Sliders)
st.sidebar.header("Dimensões do Perfil")

# Valores baseados no seu comparativo padrão
largura = st.sidebar.slider("Largura da Base (mm)", 1.0, 30.0, 10.60, step=0.1)
altura = st.sidebar.slider("Altura Total (mm)", 1.0, 30.0, 5.30, step=0.1)
raio_canto = st.sidebar.slider("Raios de Canto (mm)", 0.0, 2.0, 0.45, step=0.05)

st.sidebar.divider()
st.sidebar.subheader("Propriedades do Material")
# Densidade padrão para Aço Inox (ex: 304/316)
densidade = st.sidebar.number_input("Densidade (g/cm³)", value=8.50, format="%.2f")

# 3. Motor Geométrico 
def gerar_perfil_triangular(b, h, r):
    """
    Gera um triângulo isósceles compensando o raio para que as 
    dimensões finais (b, h) correspondam exatamente ao input do usuário.
    """
    # Coordenadas do polígono interno (compensado pelo raio)
    x_base_dir = (b / 2) - r
    x_base_esq = -(b / 2) + r
    y_base = r
    y_topo = h - r
    
    # Trava de segurança: impede que a geometria quebre se o usuário colocar um raio maior que a peça
    if x_base_dir <= 0 or y_topo <= y_base:
        return Polygon() 
        
    # Desenha o triângulo base
    base_triangle = Polygon([
        (x_base_esq, y_base), 
        (x_base_dir, y_base), 
        (0, y_topo) # Vértice superior centrado
    ])
    
    # Aplica o arredondamento (buffer)
    if r > 0:
        return base_triangle.buffer(r)
    return base_triangle

# Gera a geometria
perfil = gerar_perfil_triangular(largura, altura, raio_canto)

# 4. Cálculos e Renderização
if perfil.is_empty:
    st.error("⚠️ O raio inserido é incompatível com as dimensões da peça. Reduza o raio ou aumente a base/altura.")
else:
    area_mm2 = perfil.area
    peso_por_metro = area_mm2 * densidade

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Visualização em Escala 1:1")
        fig, ax = plt.subplots(figsize=(8, 5))
        x, y = perfil.exterior.xy
        
        # Paleta de cores industrial e limpa
        ax.plot(x, y, color='#1c2833', linewidth=2) # Contorno
        ax.fill(x, y, color='#aeb6bf', alpha=0.5)   # Preenchimento
        
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.6, color='#d5d8dc')
        
        # Remove molduras pesadas do gráfico
        for spine in ax.spines.values():
            spine.set_color('#bdc3c7')
            
        st.pyplot(fig)

    with col2:
        st.subheader("Resultados Físicos")
        st.metric(label="Área da Seção", value=f"{area_mm2:.3f} mm²")
        st.metric(label="Peso Linear", value=f"{peso_por_metro:.1f} g/m")
        
    # 5. Exportação para PDF Vetorial
    def criar_pdf(figura):
        buf = io.BytesIO()
        figura.savefig(buf, format="pdf", bbox_inches="tight")
        buf.seek(0)
        return buf

    st.sidebar.divider()
    st.sidebar.subheader("Documentação")
    st.sidebar.download_button(
        label="📄 Baixar Desenho (PDF)",
        data=criar_pdf(fig),
        file_name=f"perfil_triangular_{largura:.2f}x{altura:.2f}.pdf",
        mime="application/pdf"
    )
