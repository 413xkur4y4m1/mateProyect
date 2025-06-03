#!/usr/bin/env python3
"""
Sistema de Selección Óptima de Rutas en Red de Servidores
Universidad La Salle Nezahualcóyotl - Proyecto Integrador
Combina algoritmos de grafos y lógica difusa para optimizar rutas entre servidores
"""

import time
import json
import logging
import numpy as np
import pandas as pd
import networkx as nx
import skfuzzy as fuzz
from datetime import datetime, timedelta
from ping3 import ping
import matplotlib.pyplot as plt
import seaborn as sns

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('network_optimization.log'),
        logging.StreamHandler()
    ]
)

class NetworkMetricsCollector:
    """Módulo para recopilar métricas de red entre servidores"""
    
    def __init__(self, servers_config):
        self.servers = servers_config
        self.metrics_buffer = []
        
    def collect_latency(self, source, target, samples=10):
        """Mide latencia promedio mediante múltiples pings"""
        latencies = []
        for _ in range(samples):
            try:
                response_time = ping(target, timeout=2)
                if response_time:
                    latencies.append(response_time * 1000)  # Conversión a ms
            except Exception as e:
                self.log_error(f"Error pinging {target}: {e}")
        
        return {
            'avg_latency': np.mean(latencies) if latencies else None,
            'std_latency': np.std(latencies) if latencies else None,
            'packet_loss': (samples - len(latencies)) / samples * 100
        }
    
    def measure_availability(self, target, duration_hours=1):
        """Evalúa disponibilidad del servicio en ventana temporal"""
        successful_checks = 0
        total_checks = max(1, int(duration_hours * 12))  # Checks cada 5 minutos
        
        for _ in range(total_checks):
            if self.service_health_check(target):
                successful_checks += 1
            if total_checks > 1:
                time.sleep(300)  # 5 minutos entre checks
        
        return (successful_checks / total_checks) * 100
    
    def service_health_check(self, target):
        """Verifica si el servicio está disponible"""
        try:
            response_time = ping(target, timeout=2)
            return response_time is not None
        except:
            return False
    
    def log_error(self, message):
        logging.error(message)

class FuzzyNetworkEvaluator:
    """Módulo de evaluación de calidad de enlace usando lógica difusa"""
    
    def __init__(self):
        self.setup_membership_functions()
    
    def setup_membership_functions(self):
        """Define funciones de pertenencia para cada métrica"""
        # Latencia: Baja, Media, Alta
        self.latency_low = fuzz.trimf(np.arange(0, 201, 1), [0, 0, 100])
        self.latency_medium = fuzz.trimf(np.arange(0, 201, 1), [50, 100, 150])
        self.latency_high = fuzz.trimf(np.arange(0, 201, 1), [100, 200, 200])
        
        # Disponibilidad: Baja, Media, Alta
        self.availability_low = fuzz.trimf(np.arange(0, 101, 1), [0, 0, 95])
        self.availability_medium = fuzz.trimf(np.arange(0, 101, 1), [90, 95, 99])
        self.availability_high = fuzz.trimf(np.arange(0, 101, 1), [95, 100, 100])
        
        # Pérdida de paquetes: Baja, Media, Alta
        self.packet_loss_low = fuzz.trimf(np.arange(0, 11, 1), [0, 0, 2])
        self.packet_loss_medium = fuzz.trimf(np.arange(0, 11, 1), [1, 3, 5])
        self.packet_loss_high = fuzz.trimf(np.arange(0, 11, 1), [3, 10, 10])
    
    def evaluate_link_quality(self, latency, availability, packet_loss):
        """Calcula calidad del enlace usando inferencia difusa"""
        # Fuzzificación
        lat_low = fuzz.interp_membership(np.arange(0, 201, 1), self.latency_low, latency)
        lat_med = fuzz.interp_membership(np.arange(0, 201, 1), self.latency_medium, latency)
        lat_high = fuzz.interp_membership(np.arange(0, 201, 1), self.latency_high, latency)
        
        avail_low = fuzz.interp_membership(np.arange(0, 101, 1), self.availability_low, availability)
        avail_med = fuzz.interp_membership(np.arange(0, 101, 1), self.availability_medium, availability)
        avail_high = fuzz.interp_membership(np.arange(0, 101, 1), self.availability_high, availability)
        
        loss_low = fuzz.interp_membership(np.arange(0, 11, 1), self.packet_loss_low, packet_loss)
        loss_med = fuzz.interp_membership(np.arange(0, 11, 1), self.packet_loss_medium, packet_loss)
        loss_high = fuzz.interp_membership(np.arange(0, 11, 1), self.packet_loss_high, packet_loss)
        
        # Reglas de inferencia
        rule1 = np.fmin(np.fmin(lat_low, avail_high), loss_low)  # Calidad Excelente
        rule2 = np.fmin(np.fmin(lat_med, avail_med), loss_low)   # Calidad Buena
        rule3 = np.fmax(np.fmax(lat_high, avail_low), loss_high) # Calidad Pobre
        
        # Defuzzificación (método del centroide)
        quality_range = np.arange(0, 11, 1)
        quality_excellent = fuzz.trimf(quality_range, [7, 10, 10])
        quality_good = fuzz.trimf(quality_range, [4, 7, 10])
        quality_poor = fuzz.trimf(quality_range, [0, 3, 6])
        
        aggregated = np.fmax(np.fmax(
            np.fmin(rule1, quality_excellent),
            np.fmin(rule2, quality_good)),
            np.fmin(rule3, quality_poor))
        
        quality_score = fuzz.defuzz(quality_range, aggregated, 'centroid')
        
        # Conversión a peso (menor calidad = mayor peso para Dijkstra)
        return max(1, 11 - quality_score)

class NetworkGraphOptimizer:
    """Módulo de optimización de grafos para encontrar rutas óptimas"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.fuzzy_evaluator = FuzzyNetworkEvaluator()
    
    def build_network_graph(self, metrics_data):
        """Construye grafo ponderado con métricas difusas"""
        # Agregar nodos
        servers = ['Google_Cloud', 'AWS', 'Azure', 'Oracle_Cloud', 'Exadata_X11']
        self.graph.add_nodes_from(servers)
        
        # Agregar aristas con pesos difusos
        for i, server1 in enumerate(servers):
            for j, server2 in enumerate(servers[i+1:], i+1):
                pair_key = f"{server1}-{server2}"
                reverse_key = f"{server2}-{server1}"
                
                # Buscar métricas en ambas direcciones
                metrics = None
                if pair_key in metrics_data:
                    metrics = metrics_data[pair_key]
                elif reverse_key in metrics_data:
                    metrics = metrics_data[reverse_key]
                
                if metrics:
                    # Calcular peso usando lógica difusa
                    fuzzy_weight = self.fuzzy_evaluator.evaluate_link_quality(
                        metrics['latency'],
                        metrics['availability'],
                        metrics['packet_loss']
                    )
                    
                    self.graph.add_edge(server1, server2, weight=fuzzy_weight,
                                      latency=metrics['latency'],
                                      availability=metrics['availability'],
                                      packet_loss=metrics['packet_loss'])
    
    def find_optimal_route(self, source, destination):
        """Encuentra ruta óptima usando algoritmo de Dijkstra"""
        try:
            path = nx.shortest_path(self.graph, source, destination, weight='weight')
            path_length = nx.shortest_path_length(self.graph, source, destination, weight='weight')
            
            # Calcular métricas agregadas de la ruta
            total_latency = 0
            min_availability = 100
            max_packet_loss = 0
            
            for i in range(len(path) - 1):
                edge_data = self.graph[path[i]][path[i+1]]
                total_latency += edge_data['latency']
                min_availability = min(min_availability, edge_data['availability'])
                max_packet_loss = max(max_packet_loss, edge_data['packet_loss'])
            
            return {
                'path': path,
                'total_weight': path_length,
                'estimated_latency': total_latency,
                'min_availability': min_availability,
                'max_packet_loss': max_packet_loss
            }
        except nx.NetworkXNoPath:
            return None
    
    def compare_routes(self, source, destination, k=3):
        """Compara múltiples rutas alternativas"""
        try:
            # Obtener k rutas más cortas
            paths = list(nx.shortest_simple_paths(self.graph, source, destination, weight='weight'))
            
            route_comparison = []
            for i, path in enumerate(paths[:k]):
                path_length = nx.path_weight(self.graph, path, weight='weight')
                
                # Calcular métricas de la ruta
                total_latency = sum(self.graph[path[j]][path[j+1]]['latency'] 
                                  for j in range(len(path)-1))
                min_availability = min(self.graph[path[j]][path[j+1]]['availability'] 
                                     for j in range(len(path)-1))
                max_packet_loss = max(self.graph[path[j]][path[j+1]]['packet_loss'] 
                                    for j in range(len(path)-1))
                
                route_comparison.append({
                    'rank': i + 1,
                    'path': ' → '.join(path),
                    'total_weight': round(path_length, 2),
                    'estimated_latency': round(total_latency, 2),
                    'min_availability': round(min_availability, 2),
                    'max_packet_loss': round(max_packet_loss, 2)
                })
            
            return route_comparison
        except nx.NetworkXNoPath:
            return []

class ResultValidator:
    """Módulo de validación de resultados y cálculo de errores"""
    
    def __init__(self):
        self.predictions = []
        self.actual_measurements = []
    
    def validate_prediction(self, predicted_latency, actual_latency):
        """Valida predicción individual y calcula errores"""
        absolute_error = abs(actual_latency - predicted_latency)
        relative_error = absolute_error / actual_latency if actual_latency > 0 else 0
        percentage_error = relative_error * 100
        
        validation_result = {
            'predicted': predicted_latency,
            'actual': actual_latency,
            'absolute_error': absolute_error,
            'relative_error': relative_error,
            'percentage_error': percentage_error,
            'within_threshold': percentage_error <= 10  # Umbral del 10%
        }
        
        self.predictions.append(predicted_latency)
        self.actual_measurements.append(actual_latency)
        
        return validation_result
    
    def calculate_aggregate_metrics(self):
        """Calcula métricas agregadas de validación"""
        if not self.predictions or not self.actual_measurements:
            return None
        
        predictions = np.array(self.predictions)
        actuals = np.array(self.actual_measurements)
        
        # Métricas de error
        mae = np.mean(np.abs(actuals - predictions))  # Mean Absolute Error
        rmse = np.sqrt(np.mean((actuals - predictions) ** 2))  # Root Mean Square Error
        mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100  # Mean Absolute Percentage Error
        
        # Coeficiente de correlación
        correlation = np.corrcoef(predictions, actuals)[0, 1]
        
        # R-squared
        ss_res = np.sum((actuals - predictions) ** 2)
        ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'mae': round(mae, 3),
            'rmse': round(rmse, 3),
            'mape': round(mape, 2),
            'correlation': round(correlation, 3),
            'r_squared': round(r_squared, 3),
            'sample_size': len(self.predictions)
        }

class NetworkOptimizationSystem:
    """Sistema principal de optimización de rutas de red"""
    
    def __init__(self):
        # Configuración de servidores
        self.servers = {
            'Google_Cloud': '8.8.8.8',  # DNS de Google como ejemplo
            'AWS': '1.1.1.1',          # Cloudflare DNS como ejemplo
            'Azure': '208.67.222.222',  # OpenDNS como ejemplo
            'Oracle_Cloud': '9.9.9.9',  # Quad9 DNS como ejemplo
            'Exadata_X11': '4.4.4.4'   # Level3 DNS como ejemplo
        }
        
        self.collector = NetworkMetricsCollector(self.servers)
        self.optimizer = NetworkGraphOptimizer()
        self.validator = ResultValidator()
    
    def load_server_config(self):
        """Carga configuración de servidores desde archivo JSON"""
        try:
            with open('server_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.warning("Archivo de configuración no encontrado, usando configuración por defecto")
            return self.servers
    
    def collect_comprehensive_metrics(self, duration_hours=1):
        """Recolecta métricas comprehensivas durante período especificado"""
        logging.info(f"Iniciando recolección de métricas por {duration_hours} horas")
        
        all_metrics = {}
        server_pairs = []
        
        # Generar todas las combinaciones de pares de servidores
        server_list = list(self.servers.keys())
        for i in range(len(server_list)):
            for j in range(i + 1, len(server_list)):
                server_pairs.append((server_list[i], server_list[j]))
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=duration_hours)
        measurement_count = 0
        max_measurements = 10  # Limitar mediciones para demo
        
        while datetime.now() < end_time and measurement_count < max_measurements:
            timestamp = datetime.now().isoformat()
            
            for source, destination in server_pairs:
                source_ip = self.servers[source]
                dest_ip = self.servers[destination]
                
                # Recolectar métricas
                metrics = self.collector.collect_latency(source_ip, dest_ip, samples=3)
                availability = self.collector.measure_availability(dest_ip, duration_hours=0.1)
                
                pair_key = f"{source}-{destination}"
                if pair_key not in all_metrics:
                    all_metrics[pair_key] = []
                
                if metrics['avg_latency']:  # Solo agregar si hay datos válidos
                    all_metrics[pair_key].append({
                        'timestamp': timestamp,
                        'latency': metrics['avg_latency'],
                        'packet_loss': metrics['packet_loss'],
                        'availability': availability,
                        'jitter': metrics['std_latency'] if metrics['std_latency'] else 0
                    })
                    
                    logging.info(f"Métricas recolectadas para {pair_key}: "
                               f"Latencia={metrics['avg_latency']:.2f}ms, "
                               f"Pérdida={metrics['packet_loss']:.1f}%, "
                               f"Disponibilidad={availability:.1f}%")
            
            measurement_count += 1
            if measurement_count < max_measurements:
                time.sleep(30)  # Pausa entre ciclos de medición
        
        # Guardar datos recolectados
        self.save_metrics_data(all_metrics)
        return all_metrics
    
    def save_metrics_data(self, metrics_data):
        """Guarda datos de métricas en formato CSV y JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar en formato JSON
        with open(f'metrics_data_{timestamp}.json', 'w') as f:
            json.dump(metrics_data, f, indent=2)
        
        # Convertir a DataFrame y guardar CSV
        records = []
        for pair_key, measurements in metrics_data.items():
            for measurement in measurements:
                record = {
                    'server_pair': pair_key,
                    **measurement
                }
                records.append(record)
        
        if records:
            df = pd.DataFrame(records)
            df.to_csv(f'metrics_data_{timestamp}.csv', index=False)
        
        logging.info(f"Datos guardados en metrics_data_{timestamp}.json y .csv")
    
    def process_and_analyze(self, metrics_data):
        """Procesa datos y ejecuta análisis de optimización"""
        logging.info("Procesando datos y construyendo grafo de red")
        
        # Calcular promedios por par de servidores
        averaged_metrics = {}
        for pair_key, measurements in metrics_data.items():
            if measurements:  # Verificar que hay datos
                avg_latency = np.mean([m['latency'] for m in measurements if m['latency']])
                avg_packet_loss = np.mean([m['packet_loss'] for m in measurements])
                avg_availability = np.mean([m['availability'] for m in measurements])
                
                averaged_metrics[pair_key] = {
                    'latency': avg_latency,
                    'packet_loss': avg_packet_loss,
                    'availability': avg_availability
                }
        
        # Construir grafo de red
        self.optimizer.build_network_graph(averaged_metrics)
        
        # Análisis de rutas para todas las combinaciones
        results = {}
        server_list = list(self.servers.keys())
        
        for source in server_list:
            for destination in server_list:
                if source != destination:
                    route_key = f"{source}_to_{destination}"
                    
                    # Encontrar ruta óptima
                    optimal_route = self.optimizer.find_optimal_route(source, destination)
                    
                    if optimal_route:
                        # Comparar con rutas alternativas
                        route_comparison = self.optimizer.compare_routes(source, destination, k=3)
                        
                        results[route_key] = {
                            'optimal_route': optimal_route,
                            'alternatives': route_comparison
                        }
                        
                        logging.info(f"Ruta óptima {source} → {destination}: "
                                   f"{' → '.join(optimal_route['path'])}")
        
        return results
    
    def validate_results(self, optimization_results):
        """Valida resultados mediante mediciones reales"""
        logging.info("Iniciando validación de resultados")
        
        validation_summary = []
        
        for route_key, route_data in optimization_results.items():
            optimal_route = route_data['optimal_route']
            predicted_latency = optimal_route['estimated_latency']
            
            # Medir latencia real de la ruta recomendada
            path = optimal_route['path']
            actual_latency = self.measure_actual_route_latency(path)
            
            if actual_latency:
                validation = self.validator.validate_prediction(predicted_latency, actual_latency)
                validation['route'] = route_key
                validation['path'] = ' → '.join(path)
                validation_summary.append(validation)
                
                logging.info(f"Validación {route_key}: "
                           f"Predicho={predicted_latency:.2f}ms, "
                           f"Real={actual_latency:.2f}ms, "
                           f"Error={validation['percentage_error']:.2f}%")
        
        # Calcular métricas agregadas
        aggregate_metrics = self.validator.calculate_aggregate_metrics()
        
        return validation_summary, aggregate_metrics
    
    def measure_actual_route_latency(self, path):
        """Mide latencia real de una ruta específica"""
        total_latency = 0
        
        for i in range(len(path) - 1):
            source_server = path[i]
            dest_server = path[i + 1]
            
            if source_server in self.servers and dest_server in self.servers:
                source_ip = self.servers[source_server]
                dest_ip = self.servers[dest_server]
                
                metrics = self.collector.collect_latency(source_ip, dest_ip, samples=3)
                if metrics['avg_latency']:
                    total_latency += metrics['avg_latency']
                else:
                    return None  # Error en medición
        
        return total_latency
    
    def generate_comprehensive_report(self, optimization_results, validation_summary, aggregate_metrics):
        """Genera reporte comprehensivo de resultados"""
        report = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_routes_analyzed': len(optimization_results),
                'validation_samples': len(validation_summary)
            },
            'optimization_results': optimization_results,
            'validation_summary': validation_summary,
            'aggregate_validation_metrics': aggregate_metrics,
            'key_findings': self.extract_key_findings(optimization_results, aggregate_metrics)
        }
        
        # Guardar reporte
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f'optimization_report_{timestamp}.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logging.info(f"Reporte comprehensivo guardado en optimization_report_{timestamp}.json")
        return report
    
    def extract_key_findings(self, optimization_results, aggregate_metrics):
        """Extrae hallazgos clave del análisis"""
        findings = []
        
        # Análisis de precisión del modelo
        if aggregate_metrics:
            if aggregate_metrics['mape'] <= 10:
                findings.append(f"✓ Modelo altamente preciso: MAPE = {aggregate_metrics['mape']:.2f}%")
            else:
                findings.append(f"⚠ Precisión moderada del modelo: MAPE = {aggregate_metrics['mape']:.2f}%")
            
            findings.append(f"📊 Correlación predicción-realidad: R² = {aggregate_metrics['r_squared']:.3f}")
        
        # Análisis de rutas más eficientes
        best_routes = []
        for route_key, route_data in optimization_results.items():
            optimal_route = route_data['optimal_route']
            if len(optimal_route['path']) == 2:  # Ruta directa
                best_routes.append((route_key, optimal_route['estimated_latency']))
        
        if best_routes:
            best_routes.sort(key=lambda x: x[1])
            findings.append(f"🚀 Ruta más eficiente: {best_routes[0][0]} ({best_routes[0][1]:.1f}ms)")
        
        return findings
    
    def create_visualization(self, optimization_results):
        """Crea visualizaciones de los resultados"""
        try:
            # Gráfico de comparación de rutas
            plt.figure(figsize=(12, 8))
            
            routes = []
            latencies = []
            
            for route_key, route_data in optimization_results.items():
                optimal_route = route_data['optimal_route']
                routes.append(route_key.replace('_to_', ' → '))
                latencies.append(optimal_route['estimated_latency'])
            
            plt.barh(routes, latencies, color='skyblue', alpha=0.7)
            plt.xlabel('Latencia Estimada (ms)')
            plt.title('Comparación de Latencias por Ruta Óptima')
            plt.tight_layout()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plt.savefig(f'route_comparison_{timestamp}.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            logging.info(f"Visualización guardada en route_comparison_{timestamp}.png")
            
        except Exception as e:
            logging.error(f"Error creando visualización: {e}")

def main():
    """Función principal del sistema"""
    print("=" * 60)
    print("SISTEMA DE SELECCIÓN ÓPTIMA DE RUTAS")
    print("Universidad La Salle Nezahualcóyotl")
    print("=" * 60)
    
    # Inicializar sistema
    system = NetworkOptimizationSystem()
    
    try:
        # Fase 1: Recolección de métricas (configurar duración según necesidades)
        print("\n🔍 Fase 1: Recolectando métricas de red...")
        metrics_data = system.collect_comprehensive_metrics(duration_hours=0.5)  # 30 minutos para demo
        
        # Verificar que se recolectaron datos
        if not any(metrics_data.values()):
            print("❌ No se pudieron recolectar métricas válidas")
            return 1
        
        # Fase 2: Procesamiento y optimización
        print("\n⚙️ Fase 2: Procesando datos y optimizando rutas...")
        optimization_results = system.process_and_analyze(metrics_data)
        
        if not optimization_results:
            print("❌ No se pudieron generar rutas optimizadas")
            return 1
        
        # Fase 3: Validación
        print("\n✅ Fase 3: Validando resultados...")
        validation_summary, aggregate_metrics = system.validate_results(optimization_results)
        
        # Fase 4: Generación de reporte
        print("\n📊 Fase 4: Generando reporte comprehensivo...")
        final_report = system.generate_comprehensive_report(
            optimization_results, validation_summary, aggregate_metrics
        )
        
        # Fase 5: Crear visualizaciones
        print("\n📈 Fase 5: Creando visualizaciones...")
        system.create_visualization(optimization_results)
        
        # Mostrar resumen de resultados
        print("\n" + "=" * 60)
        print("RESUMEN DE RESULTADOS")
        print("=" * 60)
        
        if aggregate_metrics:
            print(f"📈 Precisión del modelo (MAPE): {aggregate_metrics['mape']:.2f}%")
            print(f"📊 Correlación (R²): {aggregate_metrics['r_squared']:.3f}")
            print(f"🎯 Error promedio: {aggregate_metrics['mae']:.2f}ms")
        
        print(f"🔍 Rutas analizadas: {len(optimization_results)}")
        print(f"✅ Validaciones realizadas: {len(validation_summary)}")
        
        if final_report['key_findings']:
            print("\n🔑 HALLAZGOS CLAVE:")
            for finding in final_report['key_findings']:
                print(f"   {finding}")
        
        print("\n✨ Análisis completado exitosamente!")
        
    except Exception as e:
        logging.error(f"Error durante la ejecución: {e}")
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())