import streamlit as st
import matplotlib.pyplot as plt
from shapely.geometry import box, Point
import io

st.set_page_config(page_title="Gerador de Perfis - Superfine Steel", layout="wide")
st.title("Documentação de Perfil: Tipo T")

st.sidebar.header("Parâmetros do Perfil")

with st.sidebar.form("form_parametros"):
    largura = st.number_input("Largura da Aba (mm)", value=20.00, step=0.50, format="%.2f")
    altura = st.number_input("Altura Total (mm)", value=20.00, step=0.50, format="%.2f")
    esp_aba = st.number_input("Espessura da Aba (mm)", value=3.00, step=0.10, format="%.2f")
    esp_alma = st.number_input("Espessura da Alma (mm)", value=3.00, step=0.10, format="%.2f")
    
    st.divider()
    raio_alivio = st.number_input("Raio de Alívio Interno (mm)", value=2.00, step=0.10, format="%.2f")
    raio_canto = st.number_input("Raio dos Cantos Externos (mm)", value=0.50, step=0.05, format="%.2f")
    
    st.divider()
    densidade = st.number_input("Densidade (g/cm³)", value=8.50, step=0.10, format="%.2f")
    
    submit_button = st.form_submit_button(label="Gerar Desenho Técnico")

def gerar_perfil_t(w, h, t_aba, t_alma, r_alivio, r_canto):
    # Trava de segurança
    if t_aba >= h or t_alma >= w:
        return None

    # 1. Cria os retângulos base (Aba no topo, Alma no centro)
    aba = box(-w/2, h - t_aba, w/2, h)
    alma = box(-t_alma/2, 0, t_alma/2, h - t_aba)
    perfil = aba.union(alma)
    
    # 2. Adiciona os Raios de Alívio (Cantos internos)
    if r_alivio > 0:
        # Preenchimento direito (Quadrado - Círculo)
        cx_dir = t_alma/2 + r_alivio
        cy_dir = h - t_aba - r_alivio
        quadrado_dir = box(t_alma/2, cy_dir, cx_dir, h - t_aba)
        circulo_dir = Point(cx_dir, cy_dir).buffer(r_alivio, resolution=64)
        alivio_dir = quadrado_dir.difference(circulo_dir)
        
        # Preenchimento esquerdo (Quadrado - Círculo)
        cx_esq = -t_alma/2 - r_alivio
        cy_esq = h - t_aba - r_alivio
        quadrado_esq = box(cx_esq, cy_esq, -t_alma/2, h - t_aba)
        circulo_esq = Point(cx_esq, cy_esq).buffer(r_alivio, resolution=64)
        alivio_esq = quadrado_esq.difference(circulo_esq)
        
        perfil = perfil.union(alivio_dir).union(alivio_esq)
        
    # 3. Adiciona os Raios dos Cantos (Cantos externos)
    if r_canto > 0:
        # Retrai e expande o polígono para arredondar apenas as quinas externas vivas
        perfil = perfil.buffer(-r_canto).buffer(r_canto)
        
    return perfil

if submit_button or 'perfil_t_gerado' not in st.session_state:
    st.session_state.perfil_t_gerado = gerar_perfil_t(largura, altura, esp_aba, esp_alma, raio_alivio, raio_canto)

perfil = st.session_state.perfil_t_gerado

if perfil is None:
    st.error("⚠️ As espessuras inseridas são maiores que as dimensões totais da peça.")
else:
    area_mm2 = perfil.area
    peso_por_metro = area_mm2 * densidade

    col1, col2 = st.columns([2, 1])

    with col1:
        fig, ax = plt.subplots(figsize=(8, 10))
        
        x, y = perfil.exterior.xy
        ax.plot(x, y, color='black', linewidth=1.5)
        ax.fill(x, y, color='#f0f2f6', alpha=0.5) 
        
        ax.axis('off')
        ax.set_aspect('equal')
        
        offset = max(largura, altura) * 0.15 
        
        ax.set_xlim(-largura/2 - offset*2, largura/2 + offset*4)
        ax.set_ylim(-offset*1.5, altura + offset*2)
        
        # --- COTAS ---
        # Largura Total (Topo)
        ax.plot([-largura/2, -largura/2], [altura + 0.2, altura + offset*0.8], color='gray', lw=0.8, ls=':')
        ax.plot([largura/2, largura/2], [altura + 0.2, altura + offset*0.8], color='gray', lw=0.8, ls=':')
        ax.annotate('', xy=(-largura/2, altura + offset*0.5), xytext=(largura/2, altura + offset*0.5),
                    arrowprops=dict(arrowstyle='<|-|>', color='black', shrinkA=0, shrinkB=0, lw=1))
        ax.text(0, altura + offset*0.7, f'{largura:.2f}', ha='center', va='bottom', fontsize=10)
        
        # Altura Total (Lateral Esquerda)
        ax.plot([-largura/2 - 0.2, -largura/2 - offset*1.1], [0, 0], color='gray', lw=0.8, ls=':')
        ax.plot([-largura/2 - 0.2, -largura/2 - offset*1.1], [altura, altura], color='gray', lw=0.8, ls=':')
        ax.annotate('', xy=(-largura/2 - offset, 0), xytext=(-largura/2 - offset, altura),
                    arrowprops=dict(arrowstyle='<|-|>', color='black', shrinkA=0, shrinkB=0, lw=1))
        ax.text(-largura/2 - offset*1.3, altura/2, f'{altura:.2f}', ha='right', va='center', fontsize=10, rotation=90)
        
        # Espessura da Alma (Base)
        ax.plot([-esp_alma/2, -esp_alma/2], [-0.2, -offset*0.8], color='gray', lw=0.8, ls=':')
        ax.plot([esp_alma/2, esp_alma/2], [-0.2, -offset*0.8], color='gray', lw=0.8, ls=':')
        ax.annotate('', xy=(-esp_alma/2, -offset*0.5), xytext=(esp_alma/2, -offset*0.5),
                    arrowprops=dict(arrowstyle='<|-|>', color='black', shrinkA=0, shrinkB=0, lw=1))
        ax.text(0, -offset*0.9, f'{esp_alma:.2f}', ha='center', va='top', fontsize=10)

        # Espessura da Aba (Lateral Direita)
        ax.plot([largura/2 + 0.2, largura/2 + offset*0.8], [altura, altura], color='gray', lw=0.8, ls=':')
        ax.plot([largura/2 + 0.2, largura/2 + offset*0.8], [altura - esp_aba, altura - esp_aba], color='gray', lw=0.8, ls=':')
        ax.annotate('', xy=(largura/2 + offset*0.5, altura - esp_aba), xytext=(largura/2 + offset*0.5, altura),
                    arrowprops=dict(arrowstyle='<|-|>', color='black', shrinkA=0, shrinkB=0, lw=1))
        ax.text(largura/2 + offset*0.7, altura - esp_aba/2, f'{esp_aba:.2f}', ha='left', va='center', fontsize=10)

        # Raio de Alívio
        ax.annotate(f'R{raio_alivio:.2f}', xy=(esp_alma/2 + raio_alivio*0.3, altura - esp_aba - raio_alivio*0.3), 
                    xytext=(largura/2, altura - esp_aba - offset*0.8),
                    arrowprops=dict(arrowstyle='->', connectionstyle="arc3,rad=-.2", color='black', lw=1), fontsize=10)

        # Linha de Centro
        ax.plot([0, 0], [-offset*0.5, altura + offset*0.5], color='gray', lw=0.8, ls='-.') 

        # Quadro Técnico
        texto_carimbo = (
            f"Superfine Steel Aços Inoxidáveis\n"
            f"----------------------------------------\n"
            f"Perfil Tipo T\n"
            f"Área: {area_mm2:.3f} mm²\n"
            f"Peso: {peso_por_metro:.1f} g/m\n"
            f"Densidade: {densidade:.2f} g/cm³\n"
            f"----------------------------------------\n"
            f"Desenhado por: Felipe\n"
            f"Aprovado por: Paulo"
        )
        ax.text(largura/2 + offset*1.2, altura, texto_carimbo, ha='left', va='top', 
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
        file_name=f"perfil_T_{largura:.2f}x{altura:.2f}.pdf",
        mime="application/pdf"
    )
