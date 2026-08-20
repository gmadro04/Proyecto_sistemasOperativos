import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
import os


def analyze_batch_and_plot(file_pattern, output_dir, scheduler_name):
    """
    Procesmiento de datos de la pruebas realizadas en el robot QUPA
    total de pruebas 5
    cada archivo csv de datos contiene 3000 datos, para un total de 15000 datos.
    """
    # 1. Cargar y consolidar todos los archivos que coincidan con el patrón
    archivos = glob.glob(file_pattern)
    if not archivos:
        print(f"[ERROR] No se encontraron archivos con el patrón: {file_pattern}")
        return None

    print(f"[INFO] Procesando {len(archivos)} archivos de telemetría ({scheduler_name})...")
    
    lista_df = []
    for idx, archivo in enumerate(sorted(archivos)):
        temp_df = pd.read_csv(archivo)
        temp_df['run_id'] = f"Run_{idx}"
        lista_df.append(temp_df)
        
    df = pd.concat(lista_df, ignore_index=True)
    df['delta_ms'] = df['delta_ns'] / 1e6
    df['tick_global'] = df.index # Un tick continuo para la gráfica de dispersión

    # 2. Cálculo de métricas avanzadas
    print(f"\n=== DIAGNÓSTICO ACUMULADO DE RENDIMIENTO (CONSOLIDADO - {scheduler_name}) ===")
    
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
    ax1.scatter(
        df['tick_global'],
        df['delta_ms'],
        alpha=0.3,
        s=8,
        color='#d62728'
    )

    ax1.axhline(
        200,
        color='black',
        linestyle='--',
        linewidth=2,
        label="Objetivo (200 ms)"
    )

    ax1.axhline(
        deadline_ms,
        color='orange',
        linestyle='-.',
        linewidth=1.5,
        label=f"Deadline ({deadline_ms} ms)"
    )

    ax1.set_title(f"Traza de pruebas con robots - {scheduler_name}")
    ax1.set_xlabel("Número de ciclo")
    ax1.set_ylabel("Latencia (ms)")
    ax1.legend()
    ax1.grid(True, linestyle=':', alpha=0.6)

    # Gráfica histograma de densidad
    ax2.hist(
        df['delta_ms'],
        bins=80,
        color='#d62728',
        alpha=0.7,
        edgecolor='black'
    )

    ax2.axvline(
        p99_ms,
        color='blue',
        linestyle='-.',
        linewidth=2,
        label=f"P99 ({p99_ms:.1f} ms)"
    )

    ax2.set_title(f"Distribución y latencia de cola - {scheduler_name}")
    ax2.set_xlabel("Latencia (ms)")
    ax2.set_ylabel("Frecuencia (Nº de ciclos)")
    ax2.legend()
    ax2.grid(True, linestyle=':', alpha=0.6)

    # Gráfica CDF cumulative distribution function
    datos_ordenados = np.sort(df['delta_ms'])

    if len(df) > 1:
        p = 1. * np.arange(len(df)) / (len(df) - 1)
    else:
        p = np.array([1.0])

    ax3.plot(
        datos_ordenados,
        p,
        color='#2ca02c',
        linewidth=2
    )

    ax3.axvline(
        p99_ms,
        color='blue',
        linestyle='-.',
        linewidth=1.5,
        label=f"P99 ({p99_ms:.1f} ms)"
    )

    ax3.axhline(
        0.99,
        color='gray',
        linestyle=':',
        linewidth=1.5
    )

    ax3.set_title(f"CDF - Función de distribución acumulada - {scheduler_name}")
    ax3.set_xlabel("Latencia (ms)")
    ax3.set_ylabel("Probabilidad acumulada")
    ax3.set_ylim(0, 1.05)
    ax3.legend()
    ax3.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    
    os.makedirs(output_dir, exist_ok=True)

    scheduler_lower = scheduler_name.lower()
    plot_filename = os.path.join(
        output_dir,
        f"resultadosDatos_{scheduler_lower}.png"
    )
    
    plt.savefig(plot_filename, dpi=300)
    print(f"[INFO] Panel de gráficas guardado en: {plot_filename}")
    plt.show()
    plt.close(fig)

    # Retornar las métricas para la comparación general
    return {
        "Scheduler": scheduler_name,
        "Total Ciclos": total_muestras,
        "Media (ms)": mean_ms,
        "Jitter (ms)": jitter_ms,
        "P99 (ms)": p99_ms,
        "P99.9 (ms)": p99_9_ms,
        "Pico Máximo (ms)": max_ms,
        f"Fallos >{int(deadline_ms)}ms": deadline_misses,
        "Tasa de Fallo (%)": miss_rate
    }


def compare_schedulers(metrics_cfs, metrics_fifo, output_dir):
    """
    Generación de la comparación general entre CFS y FIFO.
    """
    print("\n=== COMPARACIÓN GENERAL CFS vs FIFO ===")

    comparison_df = pd.DataFrame([
        metrics_cfs,
        metrics_fifo
    ])

    print(comparison_df.to_string(index=False))
    print("==========================================\n")

    os.makedirs(output_dir, exist_ok=True)

    # Crear figura de comparación
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))

    # 1. Media
    axes[0, 0].bar(
        comparison_df["Scheduler"],
        comparison_df["Media (ms)"]
    )
    axes[0, 0].set_title("Comparación de media - CFS vs FIFO")
    axes[0, 0].set_ylabel("Latencia media (ms)")
    axes[0, 0].grid(True, axis='y', linestyle=':', alpha=0.6)

    # 2. Jitter
    axes[0, 1].bar(
        comparison_df["Scheduler"],
        comparison_df["Jitter (ms)"]
    )
    axes[0, 1].set_title("Comparación de jitter - CFS vs FIFO")
    axes[0, 1].set_ylabel("Jitter (ms)")
    axes[0, 1].grid(True, axis='y', linestyle=':', alpha=0.6)

    # 3. P99
    axes[0, 2].bar(
        comparison_df["Scheduler"],
        comparison_df["P99 (ms)"]
    )
    axes[0, 2].set_title("Comparación P99 - CFS vs FIFO")
    axes[0, 2].set_ylabel("P99 (ms)")
    axes[0, 2].grid(True, axis='y', linestyle=':', alpha=0.6)

    # 4. P99.9
    axes[1, 0].bar(
        comparison_df["Scheduler"],
        comparison_df["P99.9 (ms)"]
    )
    axes[1, 0].set_title("Comparación P99.9 - CFS vs FIFO")
    axes[1, 0].set_ylabel("P99.9 (ms)")
    axes[1, 0].grid(True, axis='y', linestyle=':', alpha=0.6)

    # 5. Pico máximo
    axes[1, 1].bar(
        comparison_df["Scheduler"],
        comparison_df["Pico Máximo (ms)"]
    )
    axes[1, 1].set_title("Comparación de pico máximo - CFS vs FIFO")
    axes[1, 1].set_ylabel("Latencia máxima (ms)")
    axes[1, 1].grid(True, axis='y', linestyle=':', alpha=0.6)

    # 6. Tasa de fallo
    axes[1, 2].bar(
        comparison_df["Scheduler"],
        comparison_df["Tasa de Fallo (%)"]
    )
    axes[1, 2].set_title("Comparación de tasa de fallo - CFS vs FIFO")
    axes[1, 2].set_ylabel("Tasa de fallo (%)")
    axes[1, 2].grid(True, axis='y', linestyle=':', alpha=0.6)

    plt.tight_layout()

    comparison_filename = os.path.join(
        output_dir,
        "comparacion_cfs_fifo.png"
    )

    plt.savefig(comparison_filename, dpi=300)
    print(f"[INFO] Comparación general guardada en: {comparison_filename}")

    plt.show()
    plt.close(fig)

    # Guardar también las métricas en CSV
    metrics_filename = os.path.join(
        output_dir,
        "comparacion_cfs_fifo.csv"
    )

    comparison_df.to_csv(
        metrics_filename,
        index=False
    )

    print(f"[INFO] Tabla comparativa guardada en: {metrics_filename}")


if __name__ == "__main__":

    # Listar y leer archivos qupa_jitter_cfs_log.csv y qupa_jitter_fifo_log.csv

    patron_archivos_cfs = "data/*qupa_jitter_cfs_log.csv"
    patron_archivos_fifo = "data/*qupa_jitter_fifo_log.csv"

    ruta_salida_cfs = "Results/CFS/"
    ruta_salida_fifo = "Results/FIFO/"
    ruta_salida_comparacion = "Results/Comparacion/"

    # Procesamiento independiente de CFS
    metrics_cfs = analyze_batch_and_plot(
        patron_archivos_cfs,
        ruta_salida_cfs,
        "CFS"
    )

    # Procesamiento independiente de FIFO
    metrics_fifo = analyze_batch_and_plot(
        patron_archivos_fifo,
        ruta_salida_fifo,
        "FIFO"
    )

    # Comparación general entre CFS y FIFO
    if metrics_cfs is not None and metrics_fifo is not None:
        compare_schedulers(
            metrics_cfs,
            metrics_fifo,
            ruta_salida_comparacion
        )
    else:
        print("[ERROR] No fue posible realizar la comparación general.")