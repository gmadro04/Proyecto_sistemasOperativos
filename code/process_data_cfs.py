import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os

def analyze_batch_and_plot(file_pattern, output_dir):
    """
    Procesmiento de datos de la pruebas realizadas en el robot QUPA
    total de pruebas 5
    cada archivo csv de datos contiene 3000 datos, para un total de 15000 datos.
    """
    # 1. Cargar y consolidar todos los archivos que coincidan con el patrón
    archivos = glob.glob(file_pattern)
    if not archivos:
        print(f"[ERROR] No se encontraron archivos con el patrón: {file_pattern}")
        return

    print(f"[INFO] Procesando {len(archivos)} archivos de telemetría...")
    
    lista_df = []
    for idx, archivo in enumerate(sorted(archivos)):
        temp_df = pd.read_csv(archivo)
        temp_df['run_id'] = f"Run_{idx}"
        lista_df.append(temp_df)
        
    df = pd.concat(lista_df, ignore_index=True)
    df['delta_ms'] = df['delta_ns'] / 1e6
    df['tick_global'] = df.index # Un tick continuo para la gráfica de dispersión

    # 2. Cálculo de métricas avanzadas
    print("\n=== DIAGNÓSTICO ACUMULADO DE RENDIMIENTO (CONSOLIDADO) ===")
    
    total_muestras = len(df)
    mean_ms = df['delta_ms'].mean()
    jitter_ms = df['delta_ms'].std()
    max_ms = df['delta_ms'].max()
    p99_ms = np.percentile(df['delta_ms'], 99)
    p99_9_ms = np.percentile(df['delta_ms'], 99.9) 
    
    # Métrica de tiempo límite 
    # Asumimos que un retraso > 20 ms en ejecucion de instrucciones es crítico
    deadline_ms = 220.0
    deadline_misses = len(df[df['delta_ms'] > deadline_ms])
    miss_rate = (deadline_misses / total_muestras) * 100
    
    metrics = pd.DataFrame([{
        "Total Ciclos": total_muestras,
        "Media (ms)": round(mean_ms, 2),
        "Jitter (ms)": round(jitter_ms, 2),
        "P99 (ms)": round(p99_ms, 2),
        "P99.9 (ms)": round(p99_9_ms, 2),
        "Pico Máximo (ms)": round(max_ms, 2),
        f"Fallos >{int(deadline_ms)}ms": deadline_misses,
        "Tasa de Fallo (%)": round(miss_rate, 3)
    }])
    
    print(metrics.to_string(index=False))
    print("==========================================================\n")

    # 3. Generación del panel de gráficas en grilla 1x3
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

    # Gráfica dispersión continua 
    ax1.scatter(df['tick_global'], df['delta_ms'], alpha=0.3, s=8, color='#d62728')
    ax1.axhline(200, color='black', linestyle='--', linewidth=2, label="Objetivo (200 ms)")
    ax1.axhline(deadline_ms, color='orange', linestyle='-.', linewidth=1.5, label=f"Deadline ({deadline_ms} ms)")
    ax1.set_title("Traza de pruebas con robots - CFS")
    ax1.set_xlabel("Número de ciclo")
    ax1.set_ylabel("Latencia (ms)")
    ax1.legend()
    ax1.grid(True, linestyle=':', alpha=0.6)

    # Gráfica histograma de densidad
    ax2.hist(df['delta_ms'], bins=80, color='#d62728', alpha=0.7, edgecolor='black')
    ax2.axvline(p99_ms, color='blue', linestyle='-.', linewidth=2, label=f"P99 ({p99_ms:.1f} ms)")
    ax2.set_title("Distribución y latencia de cola")
    ax2.set_xlabel("Latencia (ms)")
    ax2.set_ylabel("Frecuencia (Nº de ciclos)")
    ax2.legend()
    ax2.grid(True, linestyle=':', alpha=0.6)

    # Gráfica CDF cumulative distribution function
    datos_ordenados = np.sort(df['delta_ms'])
    p = 1. * np.arange(len(df)) / (len(df) - 1)
    ax3.plot(datos_ordenados, p, color='#2ca02c', linewidth=2)
    ax3.axvline(p99_ms, color='blue', linestyle='-.', linewidth=1.5, label=f"P99 ({p99_ms:.1f} ms)")
    ax3.axhline(0.99, color='gray', linestyle=':', linewidth=1.5)
    ax3.set_title("CDF - Función de distribución aumulada")
    ax3.set_xlabel("Latencia (ms)")
    ax3.set_ylabel("Probabilidad acumulada")
    ax3.set_ylim(0, 1.05)
    ax3.legend()
    ax3.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)
    plot_filename = os.path.join(output_dir, "resultadosDatos_cfs.png")
    
    plt.savefig(plot_filename, dpi=300)
    print(f"[INFO] Panel de gráficas guardado en: {plot_filename}")
    plt.show()

if __name__ == "__main__":
    # Listar y leer archivos qupa_jitter_cfs_log.csv
    patron_archivos = "data/*qupa_jitter_cfs_log.csv"
    ruta_salida = "Results/" 
    
    analyze_batch_and_plot(patron_archivos, ruta_salida)