import random
from geopy.distance import geodesic
from functools import lru_cache

# Função para calcular a distância total de uma rota com cache
@lru_cache(maxsize=None)
def calcular_distancia_cache(cidade1, cidade2):
    return geodesic(cidade1, cidade2).km

# Função para calcular a distância total de uma rota, usando o cache
def calcular_distancia_total(rotas, cidades):
    distancia_total = 0
    for i in range(len(rotas)):
        cidade_atual = cidades[rotas[i]]
        proxima_cidade = cidades[rotas[(i + 1) % len(rotas)]]
        distancia_total += calcular_distancia_cache(cidade_atual, proxima_cidade)
    return distancia_total

# Função para criar uma rota inicial, respeitando as prioridades
def criar_rota_priorizada(cidades, prioridades):
    cidades_prioridade_1 = [i for i, p in enumerate(prioridades) if p == 1]
    cidades_prioridade_2 = [i for i, p in enumerate(prioridades) if p == 2]
    cidades_prioridade_3 = [i for i, p in enumerate(prioridades) if p == 3]
    
    random.shuffle(cidades_prioridade_1)
    random.shuffle(cidades_prioridade_2)
    random.shuffle(cidades_prioridade_3)

    rota = cidades_prioridade_1 + cidades_prioridade_2 + cidades_prioridade_3
    return rota

# Função para criar uma população inicial, respeitando as prioridades
def criar_populacao_priorizada(cidades, prioridades, tamanho_populacao):
    populacao = [criar_rota_priorizada(cidades, prioridades) for _ in range(tamanho_populacao)]
    return populacao

# Função de seleção por torneio
def torneio(populacao, cidades, k=3):
    torneio_participantes = random.sample(populacao, k)
    melhor = min(torneio_participantes, key=lambda rota: calcular_distancia_total(rota, cidades))
    return melhor

# Função de crossover que respeita as prioridades e garante a visita de todas as cidades
def crossover_priorizado(pai1, pai2, prioridades):
    tamanho = len(pai1)
    filho = [-1] * tamanho
    ponto1, ponto2 = sorted(random.sample(range(tamanho), 2))
    
    filho[ponto1:ponto2] = pai1[ponto1:ponto2]

    # Preencher com genes do pai2 sem repetição
    for i in range(tamanho):
        if pai2[i] not in filho:
            for j in range(tamanho):
                if filho[j] == -1:
                    filho[j] = pai2[i]
                    break

    # Garantir que todas as cidades sejam visitadas
    for i in range(tamanho):
        if filho[i] == -1:
            filho[i] = pai2[i]
    
    return filho

# Função de mutação que respeita as prioridades e garante que todas as cidades sejam visitadas
def mutacao_priorizada(rota, prioridades, taxa_mutacao):
    if random.random() < taxa_mutacao:
        i, j = random.sample(range(len(rota)), 2)
        # Garantir que as cidades ainda tenham suas prioridades corretas
        if prioridades[rota[i]] == prioridades[rota[j]]:
            rota[i], rota[j] = rota[j], rota[i]
    return rota

# Função para evoluir a população com elitismo
def evoluir_priorizado(populacao, cidades, prioridades, taxa_mutacao, elitismo=1):
    populacao_ordenada = sorted(populacao, key=lambda rota: calcular_distancia_total(rota, cidades))
    nova_populacao = populacao_ordenada[:elitismo]
    
    while len(nova_populacao) < len(populacao):
        pai1 = torneio(populacao, cidades)
        pai2 = torneio(populacao, cidades)
        filho = crossover_priorizado(pai1, pai2, prioridades)
        filho = mutacao_priorizada(filho, prioridades, taxa_mutacao)
        nova_populacao.append(filho)
    
    return nova_populacao

# Função principal que roda o algoritmo genético
def algoritmo_genetico(cidades, prioridades, tamanho_populacao, numero_geracoes, taxa_mutacao, elitismo=1):
    populacao = criar_populacao_priorizada(cidades, prioridades, tamanho_populacao)
    melhor_rota = min(populacao, key=lambda rota: calcular_distancia_total(rota, cidades))

    for geracao in range(1, numero_geracoes + 1):
        populacao = evoluir_priorizado(populacao, cidades, prioridades, taxa_mutacao, elitismo)
        melhor_da_geracao = min(populacao, key=lambda rota: calcular_distancia_total(rota, cidades))
        
        if calcular_distancia_total(melhor_da_geracao, cidades) < calcular_distancia_total(melhor_rota, cidades):
            melhor_rota = melhor_da_geracao
        
        print(f"Geração {geracao}: Melhor distância = {calcular_distancia_total(melhor_rota, cidades):.2f} km")

    return melhor_rota
