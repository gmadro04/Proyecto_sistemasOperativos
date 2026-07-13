import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Parámetros del experimento
FRECUENCIA_HZ = 5.0
CICLO_IDEAL_NS = int((1.0 / FRECUENCIA_HZ) * 1e9)  # 200,000,000 ns (200 ms)
NUM_CICLOS = 1000

# Semilla para reproducibilidad
np.random.seed(42)

def generar_datos_sinteticos():
    """Genera latencias en nanosegundos basadas en perfiles de planificadores Linux."""
    
    # 1. CFS distribución normal ajustada con ruido bajo para la prueba de concepto
    cfs_ideal = np.random.normal(loc=CICLO_IDEAL_NS, scale=1.5e6, size=NUM_CICLOS)
    
    # 2. CFS sometido a estrés es decir con ruido base y picos severos por preemptions del kernel
    cfs_estres = np.random.normal(loc=CICLO_IDEAL_NS + 5e6, scale=4e6, size=NUM_CICLOS)
    # Introducir picos aleatorios que simulan los tail latency simulando cambios de respuesta por interrupciones del kernel
    picos_idx = np.random.choice(NUM_CICLOS, size=int(NUM_CICLOS * 0.05), replace=False)
    cfs_estres[picos_idx] += np.random.uniform(30e6, 80e6, size=len(picos_idx)) # Picos de 30-80ms
    
    # 3. Real-time SCHED_FIFO con Afinidad con esto damos alta prioridad ignorando el ruido del kernel, simulando un escenario de aislamiento
    rt_estres = np.random.normal(loc=CICLO_IDEAL_NS + 0.5e6, scale=0.5e6, size=NUM_CICLOS)
    # micro-picos por interrupciones no enmascarables (NMI)
    nmi_idx = np.random.choice(NUM_CICLOS, size=int(NUM_CICLOS * 0.01), replace=False)
    rt_estres[nmi_idx] += np.random.uniform(2e6, 5e6, size=len(nmi_idx))

    return pd.DataFrame({
        'ciclo': np.arange(NUM_CICLOS),
        'cfs_ideal_ns': cfs_ideal.astype(int),
        'cfs_estres_ns': cfs_estres.astype(int),
        'rt_estres_ns': rt_estres.astype(int)
    })

def analizar_y_graficar(df):
    """Calcula métricas clave y genera la visualización del Jitter."""
    
    # Convertir a milisegundos para las unidades de la grafica
    cols = ['cfs_ideal_ns', 'cfs_estres_ns', 'rt_estres_ns']
    for col in cols:
        df[col.replace('_ns', '_ms')] = df[col] / 1e6
        
    print("=== MÉTRICAS DE JITTER (Desviación estándar) ===")
    print(f"CFS Ideal:         {df['cfs_ideal_ms'].std():.2f} ms")
    print(f"CFS con Estrés:    {df['cfs_estres_ms'].std():.2f} ms (¡Problema Crítico!)")
    print(f"Real-Time + Aislamiento: {df['rt_estres_ms'].std():.2f} ms (Solución)")
    
    # Generar Gráfica
    plt.figure(figsize=(12, 6))
    
    plt.plot(df['ciclo'], df['cfs_estres_ms'], color='#d9534f', alpha=0.8, linewidth=1.2, label='Planificador CFS (Bajo Estrés)')
    plt.plot(df['ciclo'], df['rt_estres_ms'], color='#5cb85c', alpha=0.9, linewidth=1.5, label='Planificador Real-Time SCHED_FIFO (Bajo Estrés)')
    
    plt.axhline(y=200, color='black', linestyle='--', linewidth=2, label='Target Ideal (200 ms)')
    
    plt.title('Impacto del planificador del Kernel en el bucle de control (Simulación Raspbian OS)', fontsize=14, fontweight='bold')
    plt.xlabel('Número de ciclo (Ticks)', fontsize=12)
    plt.ylabel('Latencia del ciclo _step() (ms)', fontsize=12)
    plt.legend(loc='upper right')
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.tight_layout()
    
    plt.savefig('assets/analisis_jitter_qupa.png', dpi=300)
    print("\nGráfica guardada como 'analisis_jitter_qupa.png'")

if __name__ == "__main__":
    datos = generar_datos_sinteticos()
    datos.to_csv('qupa_jitter_synthetic.csv', index=False)
    analizar_y_graficar(datos)