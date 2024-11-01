import pygame
import json
from genetic_algorithm import algoritmo_genetico, evoluir_priorizado, criar_populacao_priorizada, calcular_distancia_total
import pandas as pd

# Inicializando o pygame
pygame.init()
LARGURA_TELA = 1280
ALTURA_TELA = 720
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
clock = pygame.time.Clock()
running = True

# Configurações da tela
BRANCO = (255, 255, 255)
VERMELHO = (255, 0, 0)
PRETO = (0, 0, 0)

# Divisão da tela
LARGURA_COLUNA = LARGURA_TELA // 3
ALTURA_SUPERIOR = ALTURA_TELA // 2
ALTURA_INFERIOR = ALTURA_TELA - ALTURA_SUPERIOR

# Dimensões do quadrado para o gráfico
TAMANHO_QUADRADO = min(LARGURA_TELA // 2, ALTURA_INFERIOR - 40)  # 40 para a margem inferior de 20 e superior
MARGEM_INFERIOR = 20  # Margem inferior de 20 pixels

# Tela em Branco
tela.fill(BRANCO)
# Fonte para renderizar o texto
fonte = pygame.font.Font(None, 12)
fonte1 = pygame.font.Font(None, 18)

def carregar_dados_json_prioridade(caminho_arquivo, aletoriedade=10):
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
    df_aleatorios = df_hospitais.query('Prioridade != 1').sample(n=(aletoriedade -1), random_state=42)
    nova_linha     = df_hospitais.query('Prioridade == 1')
    df_aleatorios = pd.concat([df_aleatorios, nova_linha], ignore_index=True)
   
    return [tuple(coord) for coord in df_aleatorios[['Latitude', 'Longitude']].values], df_aleatorios['Prioridade'].tolist(), df_aleatorios['Nome'].tolist(), df_aleatorios

# Função para normalizar as coordenadas geográficas dentro de um quadrado, mantendo proporções
def normalizar_coordenadas(coordenadas, largura_quadrado, altura_quadrado, margem_inferior=20):
    latitudes = [lat for lat, lon in coordenadas]
    longitudes = [lon for lat, lon in coordenadas]

    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lon, max_lon = min(longitudes), max(longitudes)

    # Calcular a escala para manter proporções
    escala_lat = altura_quadrado / (max_lat - min_lat)
    escala_lon = largura_quadrado / (max_lon - min_lon)
    
    escala = min(escala_lat, escala_lon)  # Usar a menor escala para manter proporção

    # Offset para centralizar o gráfico no quadrado
    offset_x = (LARGURA_TELA - largura_quadrado) // 2
    offset_y = ALTURA_TELA - altura_quadrado - margem_inferior

    def normalizar(lat, lon):
        # Normalizar latitude e longitude para o intervalo do quadrado menor
        x = int((lon - min_lon) * escala) + offset_x
        y = int((lat - min_lat) * escala) + offset_y
        return x, y
    
    return [normalizar(lat, lon) for lat, lon in coordenadas]

# Função para desenhar os pontos e as rotas no quadrado menor
def desenhar_rota(tela, coordenadas_normalizadas, rota):
    # Preencher a área específica (parte inferior)
    pygame.draw.rect(tela, BRANCO, (0, ALTURA_SUPERIOR, LARGURA_TELA, ALTURA_INFERIOR))
    
    # Desenhar a rota conectando os pontos
    for i in range(len(rota)):
        x_atual, y_atual = coordenadas_normalizadas[rota[i]]
        x_proximo, y_proximo = coordenadas_normalizadas[rota[(i + 1) % len(rota)]]
        
        # Conectar os pontos com linhas
        pygame.draw.line(tela, PRETO, (x_atual, y_atual), (x_proximo, y_proximo), 2)
        
        # Desenhar os pontos
        pygame.draw.circle(tela, VERMELHO, (x_atual, y_atual), 5)
    
    pygame.display.flip()

# Função para exibir os hospitais carregados no pygame
def exibir_hospitais_pygame(dados_hospitais):
    y_offset = 50
    pygame.draw.rect(tela, BRANCO, (0, 0, LARGURA_COLUNA, ALTURA_SUPERIOR))  # Preenche a primeira coluna
    colunas_desejadas = ['Nome', 'Prioridade']
    df_selecionado = dados_hospitais[colunas_desejadas].sort_values(by='Prioridade')

    label1 = fonte1.render('Hospitais Selecionados Para Analise de Rota', True, PRETO)
    tela.blit(label1, (10, 20))
    # Exibir os hospitais
    for idx, row in df_selecionado.iterrows():
        texto = f"{row['Nome']}, Prioridade: {row['Prioridade']}"
        label = fonte.render(texto, True, PRETO)
        tela.blit(label, (10, y_offset))
        y_offset += 15  # Ajusta o espaço entre as linhas
        if y_offset > ALTURA_SUPERIOR - 50:  # Evitar que o texto saia da tela
            break
    pygame.display.flip()

# Função para exibir a melhor rota com os nomes e prioridades dos locais no pygame
def exibir_melhor_rota_pygame(melhor_rota, nomes, prioridades):
    y_offset = 50
    pygame.draw.rect(tela, BRANCO, (LARGURA_COLUNA, 0, LARGURA_COLUNA, ALTURA_SUPERIOR))  # Preenche a segunda coluna
    label1 = fonte1.render('Melhor Rota Encontrada', True, PRETO)
    tela.blit(label1, (LARGURA_COLUNA + 10, 20))
    for i in melhor_rota:
        texto = f"{nomes[i]} (Prioridade: {prioridades[i]})"
        label = fonte.render(texto, True, PRETO)
        tela.blit(label, (LARGURA_COLUNA + 10, y_offset))
        y_offset += 15
        if y_offset > ALTURA_SUPERIOR - 50:  # Evitar que o texto saia da tela
            break
    pygame.display.flip()

# Função para exibir o progresso da melhor rota por geração no pygame
def exibir_melhor_rota_por_geracao(geracao, melhor_distancia):
    y_offset = 50
    pygame.draw.rect(tela, BRANCO, (2 * LARGURA_COLUNA, 0, LARGURA_COLUNA, ALTURA_SUPERIOR))  # Preenche a terceira coluna
    label1 = fonte1.render(f'Progresso - Geração {geracao}', True, PRETO)
    tela.blit(label1, (2 * LARGURA_COLUNA + 10, 20))
    texto = f"Melhor distância: {melhor_distancia:.2f} km"
    label = fonte.render(texto, True, PRETO)
    tela.blit(label, (2 * LARGURA_COLUNA + 10, y_offset + 30))
    pygame.display.flip()

# Função principal que roda o algoritmo genético com ponto de parada
def algoritmo_genetico_pygame(cidades, prioridades, tamanho_populacao, numero_geracoes, taxa_mutacao, elitismo=1, max_sem_melhorias=500):
    # Normalizar coordenadas geográficas para a tela
    coordenadas_normalizadas = normalizar_coordenadas(cidades, largura_quadrado=TAMANHO_QUADRADO, altura_quadrado=TAMANHO_QUADRADO, margem_inferior=MARGEM_INFERIOR)
    
    populacao = criar_populacao_priorizada(cidades, prioridades, tamanho_populacao)
    melhor_rota = min(populacao, key=lambda rota: calcular_distancia_total(rota, cidades))
    melhor_distancia = calcular_distancia_total(melhor_rota, cidades)
    
    # Variável para contar o número de gerações sem melhorias
    sem_melhorias = 0

    for geracao in range(1, numero_geracoes + 1):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                return

        # Evoluir a população
        populacao = evoluir_priorizado(populacao, cidades, prioridades, taxa_mutacao, elitismo)
        melhor_da_geracao = min(populacao, key=lambda rota: calcular_distancia_total(rota, cidades))
        distancia_atual = calcular_distancia_total(melhor_da_geracao, cidades)
        
        # Verificar se houve melhoria
        if distancia_atual < melhor_distancia:
            melhor_rota = melhor_da_geracao
            melhor_distancia = distancia_atual
            sem_melhorias = 0  # Resetar o contador de melhorias
        else:
            sem_melhorias += 1  # Incrementar se não houver melhoria

        # Se atingir o máximo de gerações sem melhorias, parar
        if sem_melhorias >= max_sem_melhorias:
            print(f"Parando após {geracao} gerações sem melhorias.")
            break

        # Atualizar a parte inferior com a nova melhor rota
        desenhar_rota(tela, coordenadas_normalizadas, melhor_rota)
        
        # Exibir o progresso da melhor rota na parte superior direita
        exibir_melhor_rota_por_geracao(geracao, melhor_distancia)

        print(f"Geração {geracao}: Melhor distância = {melhor_distancia:.2f} km")

    return melhor_rota

# Caminho para o arquivo JSON
caminho_arquivo_json = "dados_hospitais3.json"

# Carregar as coordenadas, prioridades e nomes
coordenadas, prioridades, nomes, dados_hospitais = carregar_dados_json_prioridade(caminho_arquivo_json, 20)

# Configurações do algoritmo genético
tamanho_populacao = 100
numero_geracoes = 5000  # Número máximo de gerações
taxa_mutacao = 0.05

# Rodar o algoritmo genético com visualização e ponto de parada após 100 gerações sem melhorias
if coordenadas and nomes:
    # Exibir os hospitais selecionados no pygame (primeira coluna)
    exibir_hospitais_pygame(dados_hospitais)
    
    # Avaliar a performance e encontrar a melhor rota (segunda coluna)
    melhor_rota = algoritmo_genetico_pygame(coordenadas, prioridades, tamanho_populacao, numero_geracoes, taxa_mutacao)
    
    # Exibir a melhor rota no pygame (terceira coluna)
    exibir_melhor_rota_pygame(melhor_rota, nomes, prioridades)
    
else:
    print("Erro ao carregar os dados dos hospitais.")

# Manter a janela do Pygame aberta após concluir o algoritmo
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    clock.tick(60)

pygame.quit()
