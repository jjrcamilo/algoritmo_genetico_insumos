import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.neighbors import NearestNeighbors
import json
from geopy.distance import geodesic  # Para calcular a distância geográfica entre dois pontos

# Função para carregar os dados dos hospitais de um arquivo JSON
def carregar_dados_json_prioridade(caminho_arquivo, aleatoriedade=10):
    with open(caminho_arquivo, 'r', encoding='utf-8') as file:
        dados = json.load(file)
    
    coordenadas = []
    prioridades = []
    nomes = []
    
    for item in dados:
        try:
            latitude = float(item["Geo"]["Latitude"])
            longitude = float(item["Geo"]["Longitude"])
            prioridade = int(item.get("Prioridade", 3))  # Prioridade padrão 3 se não estiver especificada
            coordenadas.append((latitude, longitude))
            prioridades.append(prioridade)
            nomes.append(item["Nome"])
        except (ValueError, KeyError) as e:
            print(f"Erro ao processar o item: {item}. Erro: {e}")
    
    df_hospitais = pd.DataFrame(coordenadas, columns=['Latitude', 'Longitude'])
    df_hospitais['Nome'] = nomes
    df_hospitais['Prioridade'] = prioridades
    df_aleatorios = df_hospitais.query('Prioridade != 1').sample(n=(aleatoriedade - 1), random_state=42)
    nova_linha = df_hospitais.query('Prioridade == 1')
    df_aleatorios = pd.concat([df_aleatorios, nova_linha], ignore_index=True)
    df_aleatorios = df_aleatorios.sort_values(by='Prioridade', ascending=True)
   
    return [np.array(coord) for coord in df_aleatorios[['Latitude', 'Longitude']].values], df_aleatorios['Prioridade'].tolist(), df_aleatorios['Nome'].tolist(), df_aleatorios

# Função para calcular o fitness (distância total da rota)
def calcular_fitness(rota, hospitais):
    distancia_total = 0.0
    for i in range(len(rota) - 1):
        ponto_atual = hospitais[rota[i]]
        proximo_ponto = hospitais[rota[i + 1]]
        distancia = geodesic(ponto_atual, proximo_ponto).km  # Distância em quilômetros
        distancia_total += distancia
    # Fechar a rota voltando ao ponto inicial
    distancia_total += geodesic(hospitais[rota[-1]], hospitais[rota[0]]).km
    return distancia_total

# Função para encontrar a melhor rota utilizando o método Nearest Neighbor com sklearn
def nearest_neighbor_sklearn(hospitais, ponto_inicial_idx=0):
    # Usar o NearestNeighbors da biblioteca sklearn para encontrar os vizinhos mais próximos
    knn = NearestNeighbors(n_neighbors=5, algorithm='auto').fit(hospitais)
    
    rota = [ponto_inicial_idx]  # Começamos do ponto inicial
    visitados = set(rota)  # Mantém o controle dos hospitais já visitados

    while len(rota) < len(hospitais):
        # Hospital atual
        hospital_atual = hospitais[rota[-1]].reshape(1, -1)

        # Encontrar o hospital mais próximo que ainda não foi visitado
        distancias, indices = knn.kneighbors(hospital_atual)
        
        proximo_hospital_idx = None
        for i in range(1, len(hospitais)):
            candidato_idx = (indices + i) % len(hospitais)
            candidato_idx = candidato_idx[0][0]
            if candidato_idx not in visitados:
                proximo_hospital_idx = candidato_idx
                break

        # Adicionar o próximo hospital à rota
        if proximo_hospital_idx is not None:
            rota.append(proximo_hospital_idx)
            visitados.add(proximo_hospital_idx)

    return rota

# Visualizar a rota no gráfico
def plotar_rota(hospitais, rota, nomes_hospitais, fitness):
    plt.figure(figsize=(10, 6))
    
    # Plotar os hospitais como pontos
    for i, nome in enumerate(nomes_hospitais):
        plt.scatter(hospitais[i][1], hospitais[i][0], c='blue')
        plt.text(hospitais[i][1] + 0.0005, hospitais[i][0] + 0.0005, nome, fontsize=9)
    
    # Desenhar as linhas conectando os hospitais na rota
    for i in range(len(rota) - 1):
        ponto_atual = hospitais[rota[i]]
        proximo_ponto = hospitais[rota[i + 1]]
        plt.plot([ponto_atual[1], proximo_ponto[1]], [ponto_atual[0], proximo_ponto[0]], 'r--')
    
    # Fechar a rota conectando o último hospital com o primeiro
    plt.plot([hospitais[rota[-1]][1], hospitais[rota[0]][1]], [hospitais[rota[-1]][0], hospitais[rota[0]][0]], 'r--')

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.title(f"Rota Encontrada Usando Nearest Neighbor - Fitness: {fitness:.2f} km")
    plt.show()

# Carregar dados dos hospitais
caminho_arquivo_json = 'dados_hospitais3.json'  # Atualize para o caminho correto do arquivo
coordenadas, prioridades, nomes_hospitais, dados_hospitais = carregar_dados_json_prioridade(caminho_arquivo_json, aleatoriedade=20)

print(dados_hospitais)
# Encontrar a rota começando do Hospital de Prioridade 1 (o primeiro no dataset)
ponto_inicial_idx = 0
rota = nearest_neighbor_sklearn(coordenadas, ponto_inicial_idx)

# Exibir a rota encontrada
print("Rota encontrada utilizando o método Nearest Neighbor (sklearn):")
for idx in rota:
    print(nomes_hospitais[idx])

# Calcular o fitness da rota
fitness = calcular_fitness(rota, coordenadas)
print(f"Fitness (Distância Total Percorrida): {fitness:.2f} km")

# Plotar a rota
plotar_rota(coordenadas, rota, nomes_hospitais, fitness)
