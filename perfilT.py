st.sidebar.header("Parâmetros do Perfil")

with st.sidebar.form("form_parametros"):
    # Cota de 5.30 agora é a extremidade total (Largura Total)
largura_total = st.number_input("Largura Total do Topo (mm)", value=5.30, step=0.10, format="%.2f")
altura = st.number_input("Altura Total (mm)", value=10.60, step=0.10, format="%.2f")

st.divider()
raio_topo = st.number_input("Raio do Topo (mm)", value=0.30, step=0.05, format="%.2f")
raio_base = st.number_input("Raio da Base (mm)", value=0.45, step=0.05, format="%.2f")
raio_conn = st.number_input("Raio de Conexão (mm)", value=0.50, step=0.05, format="%.2f")
    h_conn = st.number_input("Altura do Raio de Conexão (mm)", value=1.71, step=0.05, format="%.2f")
    
    # Atualizado o nome para deixar claro no sistema
    h_conn = st.number_input("Altura de Tangência (mm)", value=1.71, step=0.05, format="%.2f", help="Medido do centro do raio superior até o ponto de tangência do raio de conexão")

st.divider()
    # Ângulo a partir da linha de centro (vertical)
angulo_sup = st.number_input("Ângulo Rampa Superior (°)", value=39.0, step=0.5, format="%.1f")
densidade = st.number_input("Densidade (g/cm³)", value=8.50, step=0.10, format="%.2f")

submit_button = st.form_submit_button(label="Gerar Desenho Técnico")

def gerar_perfil_t_rampas(w_total, h, r_top, r_base, r_conn, h_conn, ang_sup_deg):
def gerar_perfil_t_rampas(w_total, h, r_top, r_base, r_conn, h_conn_dim, ang_sup_deg):
try:
alpha = math.radians(ang_sup_deg)

        # 1. Topo (Calcula os centros baseado na extremidade total w_total)
        # 1. Topo
x_tr = (w_total / 2) - r_top
y_tr = h - r_top

        # Vetor normal da rampa superior
n1_x = math.cos(alpha)
n1_y = -math.sin(alpha)
        
        # Ponto de tangência no raio do topo
t1_x = x_tr + r_top * n1_x
t1_y = y_tr + r_top * n1_y

        # Vetor direção da rampa (apontando para baixo)
v1_x = -math.sin(alpha)
v1_y = -math.cos(alpha)

        # 2. Centro do Raio de Conexão
        y_cc = h - h_conn
        t_dist = (y_cc - t1_y - r_conn * n1_y) / v1_y
        x_cc = t1_x + t_dist * v1_x + r_conn * n1_x
        # 2. NOVA LÓGICA DE TANGÊNCIA (Baseada no CAD)
        # O Ponto de tangência (t2_y) fica exatamente 1.71 abaixo do centro do raio do topo (y_tr)
        t2_y = y_tr - h_conn_dim
        
        # Interseção matemática na reta para encontrar o X da tangência
        k = (t2_y - t1_y) / v1_y
        t2_x = t1_x + k * v1_x
        
        # Agora sim, recuamos a partir da tangência para encontrar o centro do raio de 0.50
        x_cc = t2_x + r_conn * n1_x
        y_cc = t2_y + r_conn * n1_y

# 3. Tangente Interna (Rampa Inferior)
dy = y_cc - r_base
@@ -61,7 +64,6 @@ def gerar_perfil_t_rampas(w_total, h, r_top, r_base, r_conn, h_conn, ang_sup_deg
gamma = math.atan2(dy, dx)
delta = math.acos((r_base + r_conn) / dist)

        # Ângulo normal da rampa inferior e cálculo do ângulo em graus
phi = gamma - delta 
n2_x = math.cos(phi)
n2_y = math.sin(phi)
@@ -97,30 +99,33 @@ def arc(cx, cy, r, a1, a2, cw=True, steps=30):
left_half = [(-x, y) for x, y in reversed(right_half)]
poly_points = right_half + left_half[1:-1]

        # Dados extras exportados para desenhar as cotas corretamente
tangentes = {
't1': (t1_x, t1_y),
'v1': (v1_x, v1_y),
't3': (x_cc - r_conn*n2_x, y_cc - r_conn*n2_y),
'v2': (-math.sin(phi), -math.cos(phi))
}

        return Polygon(poly_points), ang_inf_deg, (x_tr, y_tr, x_cc, y_cc), tangentes
        # Retornando t2_x e t2_y para desenhar a cota perfeitamente
        return Polygon(poly_points), ang_inf_deg, (x_tr, y_tr, x_cc, y_cc, t2_x, t2_y), tangentes

except Exception as e:
return None, None, None, None

if submit_button or 'perfil_t_calc' not in st.session_state:
    st.session_state.perfil_t_calc = gerar_perfil_t_rampas(largura_total, altura, raio_topo, raio_base, raio_conn, h_conn, angulo_sup)
# Mudei a variável para _v3 para limpar a memória do Streamlit e não dar aquele erro vermelho
if submit_button or 'perfil_t_calc_v3' not in st.session_state:
    st.session_state.perfil_t_calc_v3 = gerar_perfil_t_rampas(largura_total, altura, raio_topo, raio_base, raio_conn, h_conn, angulo_sup)

perfil, angulo_inf_calculado, centros, tangentes = st.session_state.perfil_t_calc
perfil, angulo_inf_calculado, centros, tangentes = st.session_state.perfil_t_calc_v3

if perfil is None:
st.error("⚠️ As medidas fornecidas não formam uma geometria tangencial válida. Verifique os raios e ângulos.")
else:
area_mm2 = perfil.area
peso_por_metro = area_mm2 * densidade
    x_tr, y_tr, x_cc, y_cc = centros
    
    # Desempacotando as coordenadas de tangência
    x_tr, y_tr, x_cc, y_cc, t2_x, t2_y = centros

col1, col2 = st.columns([2, 1])

@@ -138,35 +143,30 @@ def arc(cx, cy, r, a1, a2, cw=True, steps=30):
ax.set_xlim(-largura_total/2 - offset*3, largura_total/2 + offset*4.5)
ax.set_ylim(-offset, altura + offset*1.5)

        # Linha de Centro
ax.plot([0, 0], [-offset*0.5, altura + offset*0.8], color='#ff00ff', lw=0.8, ls='-.')
        
        # Cruzes dos Centros
ax.plot([-x_tr, x_tr], [y_tr, y_tr], marker='+', color='#ff00ff', markersize=8, ls='None')
ax.plot([-x_cc, x_cc], [y_cc, y_cc], marker='+', color='#ff00ff', markersize=8, ls='None')
ax.plot([0], [raio_base], marker='+', color='#ff00ff', markersize=8, ls='None')

# --- COTAS LINEARES ---
        # Largura Total (Extremidades)
ax.plot([-largura_total/2, -largura_total/2], [altura, altura + offset*0.6], color='green', lw=0.8, ls='-')
ax.plot([largura_total/2, largura_total/2], [altura, altura + offset*0.6], color='green', lw=0.8, ls='-')
ax.annotate('', xy=(-largura_total/2, altura + offset*0.4), xytext=(largura_total/2, altura + offset*0.4),
arrowprops=dict(arrowstyle='<|-|>', color='green', shrinkA=0, shrinkB=0, lw=1))
ax.text(0, altura + offset*0.5, f'{largura_total:.2f}', ha='center', va='bottom', fontsize=10, color='green')

        # Altura Total
ax.plot([x_tr + 0.5, largura_total/2 + offset*1.5], [altura, altura], color='green', lw=0.8, ls='-')
ax.plot([0.5, largura_total/2 + offset*1.5], [0, 0], color='green', lw=0.8, ls='-')
ax.annotate('', xy=(largura_total/2 + offset*1.2, 0), xytext=(largura_total/2 + offset*1.2, altura),
arrowprops=dict(arrowstyle='<|-|>', color='green', shrinkA=0, shrinkB=0, lw=1))
ax.text(largura_total/2 + offset*1.4, altura/2, f'{altura:.2f}', ha='left', va='center', fontsize=10, color='green', rotation=90)

        # Altura Conexão 1.71
        ax.plot([-x_tr - 0.5, -largura_total/2 - offset*1.5], [altura, altura], color='green', lw=0.8, ls='-')
        ax.plot([-x_cc - 0.5, -largura_total/2 - offset*1.5], [y_cc, y_cc], color='green', lw=0.8, ls='-')
        ax.annotate('', xy=(-largura_total/2 - offset*1.2, y_cc), xytext=(-largura_total/2 - offset*1.2, altura),
        # COTA DE 1.71 ATUALIZADA (Medindo da cruz rosa até a tangência)
        ax.plot([-x_tr - 0.5, -largura_total/2 - offset*1.5], [y_tr, y_tr], color='green', lw=0.8, ls='-')
        ax.plot([-t2_x - 0.5, -largura_total/2 - offset*1.5], [t2_y, t2_y], color='green', lw=0.8, ls='-')
        ax.annotate('', xy=(-largura_total/2 - offset*1.2, t2_y), xytext=(-largura_total/2 - offset*1.2, y_tr),
arrowprops=dict(arrowstyle='<|-|>', color='green', shrinkA=0, shrinkB=0, lw=1))
        ax.text(-largura_total/2 - offset*1.4, (altura + y_cc)/2, f'{h_conn:.2f}', ha='right', va='center', fontsize=10, color='green', rotation=90)
        ax.text(-largura_total/2 - offset*1.4, (y_tr + t2_y)/2, f'{h_conn:.2f}', ha='right', va='center', fontsize=10, color='green', rotation=90)

# Raios
ax.annotate(f'R{raio_topo:.2f}', xy=(-x_tr, y_tr+raio_topo), xytext=(-largura_total/2 - offset, altura + offset*0.2),
@@ -176,27 +176,24 @@ def arc(cx, cy, r, a1, a2, cw=True, steps=30):
ax.annotate(f'R{raio_base:.2f}', xy=(0, 0), xytext=(-offset*1.5, -offset*0.5),
arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')

        # --- COTAS DE ÂNGULO (Arcos baseados na linha de centro) ---
        # --- COTAS DE ÂNGULO ---
t1_x, t1_y = tangentes['t1']
v1_x, v1_y = tangentes['v1']
t3_x, t3_y = tangentes['t3']
v2_x, v2_y = tangentes['v2']

        # Arco Superior (39°)
if v1_x != 0:
            y_int_sup = t1_y - t1_x * (v1_y / v1_x) # Interseção da rampa superior com X=0
            y_int_sup = t1_y - t1_x * (v1_y / v1_x)
raio_arco_sup = abs(y_int_sup - y_cc) * 0.8
arco_sup = patches.Arc((0, y_int_sup), raio_arco_sup*2, raio_arco_sup*2, 
theta1=90-angulo_sup, theta2=90, color='green', lw=1)
ax.add_patch(arco_sup)
            # Posição do texto do ângulo
txt_x_sup = (raio_arco_sup + 0.3) * math.sin(math.radians(angulo_sup/2))
txt_y_sup = y_int_sup - (raio_arco_sup + 0.3) * math.cos(math.radians(angulo_sup/2))
ax.text(txt_x_sup, txt_y_sup, f'{angulo_sup:.0f}°', color='green', fontsize=10, ha='left', va='center')

        # Arco Inferior (7.73°)
if v2_x != 0:
            y_int_inf = t3_y - t3_x * (v2_y / v2_x) # Interseção da rampa inferior com X=0
            y_int_inf = t3_y - t3_x * (v2_y / v2_x)
raio_arco_inf = abs(y_int_inf - raio_base) * 0.5
arco_inf = patches.Arc((0, y_int_inf), raio_arco_inf*2, raio_arco_inf*2, 
theta1=90-angulo_inf_calculado, theta2=90, color='green', lw=1)
@@ -205,7 +202,6 @@ def arc(cx, cy, r, a1, a2, cw=True, steps=30):
txt_y_inf = y_int_inf - (raio_arco_inf + 0.3) * math.cos(math.radians(angulo_inf_calculado/2))
ax.text(txt_x_inf, txt_y_inf, f'({angulo_inf_calculado:.2f}°)', color='green', fontsize=10, ha='left', va='center')

        # Carimbo
texto_carimbo = (
f"Superfine Steel Aços Inoxidáveis\n"
f"----------------------------------------\n"
