import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def analyze_and_plot(filename):
    """
    Lee la traza bruta, calcula métricas para descubrir el comportamiento oculto 
    y genera gráficas de diagnóstico.
    """
    df = pd.read_csv(filename)
    df['delta_ms'] = df['delta_ns'] / 1e6

    print("=== DIAGNÓSTICO DE RENDIMIENTO DEL BUCLE DE CONTROL (RAW DATA) ===")
    
    mean_ms = df['delta_ms'].mean()
    jitter_ms = df['delta_ms'].std()
    max_ms = df['delta_ms'].max()
    p99_ms = np.percentile(df['delta_ms'], 99)
    p99_9_ms = np.percentile(df['delta_ms'], 99.9) # Añadimos el 99.9 para mayor rigor
    
    metrics = pd.DataFrame([{
        "Total Ticks": len(df),
        "Media (ms)": round(mean_ms, 2),
        "Jitter Global (ms)": round(jitter_ms, 2),
        "P99 (ms)": round(p99_ms, 2),
        "P99.9 (ms)": round(p99_9_ms, 2),
        "Pico Máximo (ms)": round(max_ms, 2)
    }])
    
    print(metrics.to_string(index=False))
    print("==================================================================\n")

    # --- Generación de gráficas de explorción de los datos recolectados ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Serie de tiempo puntos de dispersión para ver la densidad del ruido
    ax1.scatter(df['tick'], df['delta_ms'], alpha=0.4, s=10, color='#d62728')
    ax1.axhline(200, color='black', linestyle='--', linewidth=2, label="Frecuencia Objetivo (200 ms)")
    ax1.set_title("Traza de ejecución - Planificador CFS")
    ax1.set_xlabel("Número de ciclo (Ticks)")
    ax1.set_ylabel("Latencia (ms)")
    ax1.legend()
    ax1.grid(True, linestyle=':', alpha=0.6)

    # Histograma de Densidad 
    ax2.hist(df['delta_ms'], bins=60, color='#d62728', alpha=0.7, edgecolor='black')
    ax2.axvline(p99_ms, color='blue', linestyle='-.', linewidth=2, label=f"Percentil 99 ({p99_ms:.1f} ms)")
    ax2.set_title("Distribución de frecuencias y latencia de cola")
    ax2.set_xlabel("Latencia (ms)")
    ax2.set_ylabel("Frecuencia (Nº de ciclos)")
    ax2.legend()
    ax2.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plot_filename = "analisis_exploratorio_cfs.png"
    plt.savefig(ruta+plot_filename, dpi=300)
    print(f"[INFO] Gráfica de diagnóstico guardada como: {plot_filename}")
    
    plt.show()

if __name__ == "__main__":
    ruta = "assets/" # donde se guarda la grafica de los datos recolectados
    csv_file = "data/qupa_jitter_cfs_log.csv"
    # Analizar el dataset recolectado
    analyze_and_plot(csv_file)