ArqueSimilarity
Aplicação desktop em Python para análise de similaridade entre imagens utilizando técnicas clássicas de visão computacional.

--Sobre o Projeto

O ArqueSimilarity – OpenCV Edition é uma aplicação desktop desenvolvida em Python que permite comparar duas imagens utilizando:

- SSIM (Structural Similarity Index)

- ORB (Oriented FAST and Rotated BRIEF – OpenCV)

O sistema exibe:

Percentual individual de cada método

Média geral de similaridade

Gráfico comparativo

Histórico persistente das análasises

--Funcionalidades

✔ Interface gráfica moderna com ttkbootstrap
✔ Visualização com zoom e arraste
✔ Comparação automática das imagens
✔ Geração de gráfico com matplotlib
✔ Histórico salvo em JSON
✔ Exportação manual do histórico

--Algoritmos Utilizados
🔹 SSIM

Baseado na comparação estrutural da imagem

Trabalha em escala de cinza

Implementado via skimage.metrics

🔹 ORB (OpenCV)

Detecção de pontos-chave

Extração de descritores

Correspondência com BFMatcher

Similaridade baseada em matches válidos

📊 Cálculo Final
Similaridade Geral = (SSIM + ORB) / 2

🖥️ Interface

A aplicação é dividida em:

Área superior:

Imagem 1

Imagem 2

Área inferior:

Botões de controle

Resultado textual

Histórico

Gráfico automático

Tema utilizado:

darkly (ttkbootstrap)
--Como exportar a comparação das imagens
Histórico salvo automaticamente em:

historico.json

🚀 Roadmap / Melhorias Futuras

 Comparação com SIFT / SURF

 Exportação de relatório em PDF

 Salvamento automático do gráfico

 Comparação em lote

 Drag-and-drop de imagens

 Ajuste de peso entre SSIM e ORB

🎯 Objetivo do Projeto

Este projeto foi desenvolvido para:

Estudo de visão computacional

Demonstração prática de algoritmos clássicos

Portfólio de desenvolvimento Python

Aplicação desktop com processamento de imagem

🛠️ Tecnologias Utilizadas

Python 3

Tkinter

ttkbootstrap

OpenCV

NumPy

scikit-image

Pillow

Matplotlib
