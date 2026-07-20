import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon, Point, MultiPolygon
import math
import io
import textwrap
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
        
        tangentes = {'t1': (t1_x, t1_y), 't2': (t2_x, t2_y)}
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
        
        y_int = h - h_conn_val
        k = (y_int - t1_y) / v1_y if v1_y != 0 else 0
        x_int = t1_x + k * v1_x
        
        dx_v = x_int
        dy_v = y_int - r_base
        dist_v = math.hypot(dx_v, dy_v)
        
        gamma = math.atan2(dy_v, dx_v)
        val = max(-1.0, min(1.0, r_base / dist_v))
        delta = math.acos(val)
        
        phi = gamma - delta 
        n2_x, n2_y = math.cos(phi), math.sin(phi)
        ang_inf_deg = -math.degrees(phi)
        
        det = n1_x * n2_y - n1_y * n2_x
        if det != 0:
            dx_c = r_conn * (n2_y - n1_y) / det
            dy_c = r_conn * (n1_x - n2_x) / det
            x_cc = x_int + dx_c
            y_cc = y_int + dy_c
        else:
            x_cc, y_cc = x_int, y_int
            
        t2_x, t2_y = x_cc - r_conn * n1_x, y_cc - r_conn * n1_y
        t3_x, t3_y = x_cc - r_conn * n2_x, y_cc - r_conn * n2_y
        t4_x, t4_y = r_base * n2_x, r_base + r_base * n2_y
        
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
            't3': (t3_x, t3_y), 't4': (t4_x, t4_y),
            't_int': (x_int, y_int)
        }
        return Polygon(poly_points), ang_inf_deg, (x_tr, y_tr, x_cc, y_cc, x_int, y_int), tangentes
    except Exception as e:
        return None, None, None, None

def gerar_perfil_retangular(w, h, r):
    try:
        r = max(0.0, min(r, w/2.0, h/2.0))
        if r == 0.0:
            poly = Polygon([(-w/2, h), (w/2, h), (w/2, 0), (-w/2, 0)])
            return poly, None, None, None
        
        x_c, y_c_top, y_c_bot = w/2 - r, h - r, r
        def arc(cx, cy, radius, a1, a2, steps=32):
            return [(cx + radius * math.cos(a), cy + radius * math.sin(a)) for a in [a1 + (a2-a1)*i/steps for i in range(steps+1)]]
        
        tr = arc(x_c, y_c_top, r, 0, math.pi/2)
        tl = arc(-x_c, y_c_top, r, math.pi/2, math.pi)
        bl = arc(-x_c, y_c_bot, r, math.pi, 3*math.pi/2)
        br = arc(x_c, y_c_bot, r, 3*math.pi/2, 2*math.pi)
        
        poly = Polygon(tr + tl + bl + br)
        return poly, None, (x_c, y_c_top, y_c_bot), None
    except:
        return None, None, None, None

def gerar_perfil_redondo(d):
    try:
        cx, cy = 0, d/2
        r = d/2
        pts = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [2*math.pi*i/64 for i in range(65)]]
        poly = Polygon(pts)
        return poly, None, (cx, cy), None
    except:
        return None, None, None, None

# ==========================================
# 2. MÓDULOS DE RENDERIZAÇÃO E CARIMBO
# ==========================================
def formatar_eixos(ax, w, h):
    offset = max(w, h) * 0.15 
    ax.axis('off')
    ax.set_aspect('equal')
    ax.set_xlim(-w/2 - offset*2.5, w/2 + offset*2.5)
    ax.set_ylim(-offset*3, h + offset*4)
    ax.plot([0, 0], [-offset*0.2, h + offset*0.2], color='#ff00ff', lw=0.8, ls='-.')
    return offset

def desenhar_margem_pagina(fig):
    margem = patches.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False, lw=1.5, edgecolor='black', transform=fig.transFigure, figure=fig)
    fig.patches.append(margem)

def desenhar_angulo_vertical(ax, p1, p2, angulo_val, pos_ratio=0.5):
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    if dx == 0: return
    
    y_apex = y1 - x1 * (dy / dx)
    y_vis = y1 + dy * pos_ratio
    x_vis = x1 + dx * pos_ratio
    
    R = math.hypot(x_vis, y_vis - y_apex)
    
    if y_vis >= y_apex:
        ang_line = math.degrees(math.atan2(y_vis - y_apex, x_vis))
        t1, t2 = ang_line, 90
        mid_ang = math.radians((t1 + t2) / 2)
    else:
        ang_line = math.degrees(math.atan2(y_vis - y_apex, x_vis))
        if ang_line < 0: ang_line += 360
        t1, t2 = 270, ang_line
        mid_ang = math.radians((t1 + t2) / 2)
        
    ax.add_patch(patches.Arc((0, y_apex), 2*R, 2*R, theta1=t1, theta2=t2, color='green', lw=1))
    
    txt_x = R * math.cos(mid_ang)
    txt_y = y_apex + R * math.sin(mid_ang)
    
    texto = f'{angulo_val:.0f}°' if abs(angulo_val - round(angulo_val)) < 0.1 else f'({angulo_val:.2f}°)'
    ax.text(txt_x, txt_y + 0.15, texto, color='green', fontsize=10, ha='center', va='bottom')

def desenhar_triangular(ax, poly, ang, centros, tangentes, w, h, kwargs):
    r_top, r_base = kwargs['r_top'], kwargs['r_base']
    offset = formatar_eixos(ax, w, h)
    gap = 0.15 
    
    x, y = poly.exterior.xy
    ax.plot(x, y, color='black', linewidth=1.5)
    ax.fill(x, y, color='#f0f2f6', alpha=0.5)
    
    xtr1, ytr1 = centros
    ax.plot([-xtr1, xtr1], [ytr1, ytr1], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax.plot([0], [r_base], marker='+', color='#ff00ff', markersize=8, ls='None')
    
    line_y = h + offset*0.4
    ax.plot([-w/2, -w/2], [h, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.plot([w/2, w/2], [h, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(-w/2, line_y), xytext=(w/2, line_y), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(0, line_y + gap, f'{w:.2f}', ha='center', va='center', fontsize=10, color='green')
    
    line_x = w/2 + offset*0.5
    ax.plot([xtr1 + 0.2, line_x + 0.2], [h, h], color='green', lw=0.8, ls='-')
    ax.plot([0.2, line_x + 0.2], [0, 0], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(line_x, 0), xytext=(line_x, h), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(line_x - gap, h/2, f'{h:.2f}', ha='center', va='center', fontsize=10, color='green', rotation=90)
    
    def get_perimeter_point(cx, cy, r, tx, ty, concave=False):
        d = math.hypot(cx - tx, cy - ty)
        if d == 0: return cx, cy
        ux, uy = (cx - tx)/d, (cy - ty)/d
        return (cx + r * ux, cy + r * uy) if concave else (cx - r * ux, cy - r * uy)
        
    tx_top, ty_top = -w/2 - offset*0.6, ytr1 + offset*0.4
    px_top, py_top = get_perimeter_point(-xtr1, ytr1, r_top, tx_top, ty_top, False)
    tx_base, ty_base = -offset*1.5, -offset*0.5
    px_base, py_base = get_perimeter_point(0, r_base, r_base, tx_base, ty_base, False)

    ax.annotate(f'R{r_top:.2f}', xy=(px_top, py_top), xytext=(tx_top, ty_top), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    ax.annotate(f'R{r_base:.2f}', xy=(px_base, py_base), xytext=(tx_base, ty_base), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    
    desenhar_angulo_vertical(ax, tangentes['t1'], tangentes['t2'], ang, pos_ratio=0.5)

def desenhar_tipo_t(ax, poly, ang, centros, tangentes, w, h, kwargs):
    r_top, r_base, r_conn, h_conn, ang_sup = kwargs['r_top'], kwargs['r_base'], kwargs['r_conn'], kwargs['h_conn'], kwargs['ang_sup']
    offset = formatar_eixos(ax, w, h)
    gap = 0.15 
    
    x, y = poly.exterior.xy
    ax.plot(x, y, color='black', linewidth=1.5)
    ax.fill(x, y, color='#f0f2f6', alpha=0.5)
    
    xtr2, ytr2, xcc2, ycc2, x_int, y_int = centros
    t1_x, t1_y = tangentes['t1']
    t2_x, t2_y = tangentes['t2']
    t3_x, t3_y = tangentes['t3']
    t4_x, t4_y = tangentes['t4']
    
    ax.plot([-xtr2, xtr2], [ytr2, ytr2], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax.plot([-xcc2, xcc2], [ycc2, ycc2], marker='+', color='#ff00ff', markersize=8, ls='None')
    ax.plot([0], [r_base], marker='+', color='#ff00ff', markersize=8, ls='None')
    
    ax.plot([-t2_x, -x_int], [t2_y, y_int], color='green', lw=0.8, ls='-')
    ax.plot([-t3_x, -x_int], [t3_y, y_int], color='green', lw=0.8, ls='-')
    
    line_y = h + offset*0.4
    ax.plot([-w/2, -w/2], [h, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.plot([w/2, w/2], [h, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(-w/2, line_y), xytext=(w/2, line_y), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(0, line_y + gap, f'{w:.2f}', ha='center', va='center', fontsize=10, color='green')
    
    line_x = w/2 + offset*0.5
    ax.plot([xtr2 + 0.2, line_x + 0.2], [h, h], color='green', lw=0.8, ls='-')
    ax.plot([0.2, line_x + 0.2], [0, 0], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(line_x, 0), xytext=(line_x, h), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(line_x - gap, h/2, f'{h:.2f}', ha='center', va='center', fontsize=10, color='green', rotation=90)
    
    line_x_h = -w/2 - offset*0.8
    ax.plot([-w/2 + 0.2, line_x_h - 0.2], [h, h], color='green', lw=0.8, ls='-') 
    ax.plot([-x_int, line_x_h - 0.2], [y_int, y_int], color='green', lw=0.8, ls='-') 
    ax.annotate('', xy=(line_x_h, y_int), xytext=(line_x_h, h), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(line_x_h - gap, (h + y_int)/2, f'{h_conn:.2f}', ha='center', va='center', fontsize=10, color='green', rotation=90)
    
    def get_perimeter_point(cx, cy, r, tx, ty, concave=False):
        d = math.hypot(cx - tx, cy - ty)
        if d == 0: return cx, cy
        ux, uy = (cx - tx)/d, (cy - ty)/d
        return (cx + r * ux, cy + r * uy) if concave else (cx - r * ux, cy - r * uy)

    tx_top, ty_top = -w/2 - offset*0.6, ytr2 + offset*0.4
    px_top, py_top = get_perimeter_point(-xtr2, ytr2, r_top, tx_top, ty_top, False)
    
    tx_conn, ty_conn = -w/2 - offset*0.7, ycc2 - offset*0.4
    px_conn, py_conn = get_perimeter_point(-xcc2, ycc2, r_conn, tx_conn, ty_conn, concave=True)
    
    tx_base, ty_base = -offset*1.5, -offset*0.5
    px_base, py_base = get_perimeter_point(0, r_base, r_base, tx_base, ty_base, False)

    ax.annotate(f'R{r_top:.2f}', xy=(px_top, py_top), xytext=(tx_top, ty_top), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    ax.annotate(f'R{r_conn:.2f}', xy=(px_conn, py_conn), xytext=(tx_conn, ty_conn), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')
    ax.annotate(f'R{r_base:.2f}', xy=(px_base, py_base), xytext=(tx_base, ty_base), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')

    desenhar_angulo_vertical(ax, (t1_x, t1_y), (t2_x, t2_y), ang_sup, pos_ratio=0.75)
    desenhar_angulo_vertical(ax, (t3_x, t3_y), (t4_x, t4_y), ang, pos_ratio=0.25)

def desenhar_retangular(ax, poly, w, h_eff, w_canvas, h_canvas, kwargs):
    r = kwargs.get('r_cantos', 0.0)
    offset = formatar_eixos(ax, w_canvas, h_canvas)
    gap = 0.15
    
    x, y = poly.exterior.xy
    ax.plot(x, y, color='black', linewidth=1.5)
    ax.fill(x, y, color='#f0f2f6', alpha=0.5)
    
    if r > 0:
        x_c, y_c_top, y_c_bot = w/2 - r, h_eff - r, r
        ax.plot([x_c, -x_c, -x_c, x_c], [y_c_top, y_c_top, y_c_bot, y_c_bot], marker='+', color='#ff00ff', markersize=8, ls='None')
        
    line_y = h_eff + offset*0.4
    ax.plot([-w/2, -w/2], [h_eff, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.plot([w/2, w/2], [h_eff, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(-w/2, line_y), xytext=(w/2, line_y), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(0, line_y + gap, f'{w:.2f}', ha='center', va='center', fontsize=10, color='green')
    
    line_x = w/2 + offset*0.5
    ax.plot([w/2 + 0.2, line_x + 0.2], [h_eff, h_eff], color='green', lw=0.8, ls='-')
    ax.plot([w/2 + 0.2, line_x + 0.2], [0, 0], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(line_x, 0), xytext=(line_x, h_eff), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(line_x - gap, h_eff/2, f'{h_eff:.2f}', ha='center', va='center', fontsize=10, color='green', rotation=90)
    
    if r > 0:
        tx, ty = -w/2 - offset*0.5, h_eff + offset*0.5
        px, py = -w/2 + r - r*math.cos(math.pi/4), h_eff - r + r*math.sin(math.pi/4)
        ax.annotate(f'R{r:.2f}', xy=(px, py), xytext=(tx, ty), arrowprops=dict(arrowstyle='->', color='green', lw=1), fontsize=10, color='green')

def desenhar_redondo(ax, poly, d, w_canvas, h_canvas):
    offset = formatar_eixos(ax, w_canvas, h_canvas)
    gap = 0.15
    
    x, y = poly.exterior.xy
    ax.plot(x, y, color='black', linewidth=1.5)
    ax.fill(x, y, color='#f0f2f6', alpha=0.5)
    
    cx, cy = 0, d/2
    ax.plot([cx], [cy], marker='+', color='#ff00ff', markersize=10, ls='None')
    
    line_y = d + offset*0.4
    ax.plot([-d/2, -d/2], [d/2, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.plot([d/2, d/2], [d/2, line_y + 0.2], color='green', lw=0.8, ls='-')
    ax.annotate('', xy=(-d/2, line_y), xytext=(d/2, line_y), arrowprops=dict(arrowstyle='<|-|>', color='green', lw=1))
    ax.text(0, line_y + gap, f'Ø {d:.2f}', ha='center', va='center', fontsize=10, color='green')

def desenhar_legenda_padrao(fig, titulo, data_str, cliente, responsavel, empresa, obs, area_info=None):
    ax_c = fig.add_axes([0.05, 0.05, 0.9, 0.12]) 
    ax_c.axis('off')
    
    ax_c.add_patch(patches.Rectangle((0, 0), 1, 1, fill=False, lw=1.5, transform=ax_c.transAxes))
    ax_c.plot([0, 1], [0.75, 0.75], color='black', lw=1, transform=ax_c.transAxes)
    ax_c.plot([0, 1], [0.50, 0.50], color='black', lw=1, transform=ax_c.transAxes)
    ax_c.plot([0, 1], [0.25, 0.25], color='black', lw=1, transform=ax_c.transAxes)
    ax_c.plot([0.5, 0.5], [0.25, 1.0], color='black', lw=1, transform=ax_c.transAxes)
    
    v_align = 'center'
    
    ax_c.text(0.02, 0.875, "PERFIL/PROJETO:", fontsize=10, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(0.20, 0.875, titulo, fontsize=10, fontweight='normal', transform=ax_c.transAxes, va=v_align)
    
    ax_c.text(0.52, 0.875, "EMPRESA:", fontsize=10, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(0.72, 0.875, empresa, fontsize=10, fontweight='normal', transform=ax_c.transAxes, va=v_align)
    
    ax_c.text(0.02, 0.625, "CLIENTE:", fontsize=10, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(0.20, 0.625, cliente, fontsize=10, fontweight='normal', transform=ax_c.transAxes, va=v_align)
    
    ax_c.text(0.52, 0.625, "RESPONSÁVEL:", fontsize=10, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(0.72, 0.625, responsavel, fontsize=10, fontweight='normal', transform=ax_c.transAxes, va=v_align)
    
    ax_c.text(0.02, 0.375, "DATA DE EMISSÃO:", fontsize=10, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    ax_c.text(0.20, 0.375, data_str, fontsize=10, fontweight='normal', transform=ax_c.transAxes, va=v_align)
    
    ax_c.text(0.52, 0.375, "ÁREA / PESO LINEAR:", fontsize=10, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    area_val = area_info if area_info else "VIDE DESENHO"
    ax_c.text(0.72, 0.375, area_val, fontsize=10, fontweight='normal', transform=ax_c.transAxes, va=v_align)
    
    ax_c.text(0.02, 0.125, "OBSERVAÇÕES:", fontsize=10, fontweight='bold', transform=ax_c.transAxes, va=v_align)
    
    obs_wrapped = textwrap.fill(obs, width=115)
    ax_c.text(0.16, 0.125, obs_wrapped, fontsize=10, fontweight='normal', transform=ax_c.transAxes, va=v_align)

# ==========================================
# 3. INTERFACE DE USUÁRIO (TOP-DOWN)
# ==========================================
st.markdown("### 1. Documentação Técnica")
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    empresa = c1.text_input("Empresa", value="Superfine Steel")
    cliente = c2.text_input("Cliente", value="")
    responsavel = c3.text_input("Responsável", value="Felipe Maia")
    data_doc = c4.date_input("Data de Emissão", value=date.today())
    obs = st.text_input("Observação", value="Tolerâncias dimensionais e de usinagem não indicadas devem seguir a norma DIN 7168.")

st.markdown("### 2. Configurações Globais")
with st.container():
    c1, c2, c3, c4 = st.columns(4)
    w_global = c1.number_input("Largura Total (mm)", value=5.30, step=0.10, format="%.2f")
    h_global = c2.number_input("Altura Total (mm)", value=10.60, step=0.10, format="%.2f")
    densidade = c3.number_input("Densidade (g/cm³)", value=8.50, step=0.10, format="%.2f")
    modo = c4.selectbox("Modo de Análise", ["Individual", "Comparativo"])

st.markdown("### 3. Parâmetros Geométricos")
perfis_disponiveis = ["Triangular", "Tipo T", "Redondo", "Quadrado", "Retangular", "Chato"]

def renderizar_inputs(modelo, prefixo):
    if modelo in ["Triangular", "Tipo T"]:
        col1, col2, col3, col4, col5 = st.columns(5)
        r_top = col1.number_input("Raio Topo (mm)", value=0.30, step=0.05, format="%.2f", key=f"{prefixo}_rtop")
        r_base = col2.number_input("Raio Base (mm)", value=0.45, step=0.05, format="%.2f", key=f"{prefixo}_rbase")
        if modelo == "Tipo T":
            r_conn = col3.number_input("Raio Conexão (mm)", value=0.50, step=0.05, format="%.2f", key=f"{prefixo}_rconn")
            h_conn = col4.number_input("Altura Intersecção (mm)", value=1.71, step=0.05, format="%.2f", key=f"{prefixo}_hconn")
            ang_sup = col5.number_input("Ângulo Superior (°)", value=39.0, step=0.5, format="%.1f", key=f"{prefixo}_ang")
            return {'r_top': r_top, 'r_base': r_base, 'r_conn': r_conn, 'h_conn': h_conn, 'ang_sup': ang_sup}
        return {'r_top': r_top, 'r_base': r_base}
    elif modelo in ["Quadrado", "Retangular", "Chato"]:
        col1, = st.columns(1)
        r_cantos = col1.number_input("Raio dos Cantos (mm)", value=0.50, step=0.05, format="%.2f", key=f"{prefixo}_rcantos")
        return {'r_cantos': r_cantos}
    elif modelo == "Redondo":
        return {}

if modo == "Individual":
    perfil_sel = st.selectbox("Selecione a Geometria", perfis_disponiveis, key="p1_sel")
    kwargs_p1 = renderizar_inputs(perfil_sel, "p1")
    titulo_base = f"Perfil {perfil_sel} {w_global:.2f} x {h_global:.2f}"
else:
    colA, colB = st.columns(2)
    with colA:
        perfil_1 = st.selectbox("Geometria Esquerda", perfis_disponiveis, index=0, key="p1_sel")
        kwargs_p1 = renderizar_inputs(perfil_1, "p1")
    with colB:
        perfil_2 = st.selectbox("Geometria Direita", perfis_disponiveis, index=1, key="p2_sel")
        kwargs_p2 = renderizar_inputs(perfil_2, "p2")
    titulo_base = f"Comparativo {w_global:.2f} x {h_global:.2f}"
    
st.divider()
submit_button = st.button("Atualizar Desenho", type="primary", use_container_width=True)

# ==========================================
# 4. GERAÇÃO DA FOLHA (PDF)
# ==========================================
if submit_button or 'app_v26_iniciado' not in st.session_state:
    st.session_state.app_v26_iniciado = True

def processar_geometria(modelo, kwargs):
    if modelo == "Triangular":
        return gerar_perfil_triangular(w_global, h_global, kwargs['r_top'], kwargs['r_base'])
    elif modelo == "Tipo T":
        return gerar_perfil_t_rampas(w_global, h_global, kwargs['r_top'], kwargs['r_base'], kwargs['r_conn'], kwargs['h_conn'], kwargs['ang_sup'])
    elif modelo == "Redondo":
        return gerar_perfil_redondo(w_global)
    elif modelo == "Quadrado":
        return gerar_perfil_retangular(w_global, w_global, kwargs.get('r_cantos', 0.0))
    elif modelo in ["Retangular", "Chato"]:
        return gerar_perfil_retangular(w_global, h_global, kwargs.get('r_cantos', 0.0))

def plotar_geometria(ax, modelo, poly, ang, centros, tangentes, kwargs):
    if modelo == "Triangular":
        desenhar_triangular(ax, poly, ang, centros, tangentes, w_global, h_global, kwargs)
    elif modelo == "Tipo T":
        desenhar_tipo_t(ax, poly, ang, centros, tangentes, w_global, h_global, kwargs)
    elif modelo == "Redondo":
        desenhar_redondo(ax, poly, w_global, w_global, h_global)
    elif modelo == "Quadrado":
        desenhar_retangular(ax, poly, w_global, w_global, w_global, h_global, kwargs)
    elif modelo in ["Retangular", "Chato"]:
        desenhar_retangular(ax, poly, w_global, h_global, w_global, h_global, kwargs)

titulo_doc = ""

if modo == "Individual":
    titulo_doc = f"Perfil {perfil_sel} {w_global:.2f} x {h_global:.2f}"
    resultado = processar_geometria(perfil_sel, kwargs_p1)
    
    if resultado[0] is None:
        st.error("Erro geométrico no perfil. Verifique as medidas.")
    else:
        poly1, ang1, cent1, tang1 = resultado
        area = poly1.area
        peso = area * densidade
        
        fig = plt.figure(figsize=(10, 14))
        desenhar_margem_pagina(fig)
        
        ax = fig.add_axes([0.1, 0.20, 0.8, 0.70]) 
        plotar_geometria(ax, perfil_sel, poly1, ang1, cent1, tang1, kwargs_p1)
        
        area_string = f"{area:.3f} mm²  /  {peso:.1f} g/m"
        desenhar_legenda_padrao(fig, titulo_base, data_doc.strftime('%d/%m/%Y'), cliente, responsavel, empresa, obs, area_string)
        
        st.pyplot(fig)

elif modo == "Comparativo":
    titulo_doc = f"Comparativo {w_global:.2f} x {h_global:.2f}"
    res1 = processar_geometria(perfil_1, kwargs_p1)
    res2 = processar_geometria(perfil_2, kwargs_p2)
    
    if res1[0] is None or res2[0] is None:
        st.error("Erro geométrico em um dos perfis.")
    else:
        poly1, ang1, cent1, tang1 = res1
        poly2, ang2, cent2, tang2 = res2
        
        area1, area2 = poly1.area, poly2.area
        reducao = ((area1 - area2) / area1) * 100 if area1 > 0 else 0
        
        fig = plt.figure(figsize=(14, 16))
        desenhar_margem_pagina(fig)
        
        ax1 = fig.add_axes([0.05, 0.20, 0.4, 0.70])
        ax2 = fig.add_axes([0.55, 0.20, 0.4, 0.70])
        
        plotar_geometria(ax1, perfil_1, poly1, ang1, cent1, tang1, kwargs_p1)
        ax1.text(0, h_global + max(w_global, h_global)*0.4, f"{area1*densidade:.1f} g/m\n(Densidade: {densidade} g/cm³)", ha='center', va='center', fontsize=12, bbox=dict(facecolor='white', edgecolor='black', pad=5))
        ax1.text(0, -max(w_global, h_global)*0.3, f"Área: {area1:.3f} mm²", ha='center', va='center', fontsize=12)
        
        plotar_geometria(ax2, perfil_2, poly2, ang2, cent2, tang2, kwargs_p2)
        ax2.text(0, h_global + max(w_global, h_global)*0.4, f"{area2*densidade:.1f} g/m\n(Densidade: {densidade} g/cm³)", ha='center', va='center', fontsize=12, bbox=dict(facecolor='white', edgecolor='black', pad=5))
        ax2.text(0, -max(w_global, h_global)*0.3, f"Área: {area2:.3f} mm²", ha='center', va='center', fontsize=12)
        
        fig.text(0.5, 0.19, f"Redução de {reducao:.2f}%" if reducao > 0 else f"Aumento de {abs(reducao):.2f}%", ha='center', va='center', fontsize=16, fontweight='bold')
        
        desenhar_legenda_padrao(fig, titulo_base, data_doc.strftime('%d/%m/%Y'), cliente, responsavel, empresa, obs)
        
        st.pyplot(fig)

def criar_pdf(figura):
    buf = io.BytesIO()
    figura.savefig(buf, format="pdf", bbox_inches="tight", pad_inches=0.2)
    buf.seek(0)
    return buf

if 'fig' in locals():
    st.download_button(
        label="📄 Fazer Download do Documento PDF",
        data=criar_pdf(fig),
        file_name=f"{titulo_base.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
