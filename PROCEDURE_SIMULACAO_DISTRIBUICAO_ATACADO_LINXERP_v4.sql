USE [Cliente386_ERP]
GO
/****** Object:  StoredProcedure [dbo].[sp_distribuicao_atacado]    Script Date: 12/08/2025 12:06:38 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- ============================================================================================
-- Autor:           Leonardo Farias
-- Data de Criação: 2024-06-14
-- Modificado em:   2024-06-17
-- Descrição:       Calcula a distribuição de estoque de atacado com base
--                  nos pedidos pendentes e no estoque disponível.
--                  A ordem de distribuição considera Prioridade e o Valor Total do Pedido.
--                  Os resultados são armazenados na tabela dbo.RESULTADO_DISTRIBUICAO_ATACADO.
-- ============================================================================================
ALTER   PROCEDURE [dbo].[sp_distribuicao_atacado]
AS
BEGIN
    SET NOCOUNT ON;

    -- 1. Garante que a tabela de resultados esteja limpa para a nova execução
    IF OBJECT_ID('dbo.RESULTADO_DISTRIBUICAO_ATACADO', 'U') IS NOT NULL
    BEGIN
        DROP TABLE dbo.RESULTADO_DISTRIBUICAO_ATACADO;
        PRINT 'Tabela dbo.ResultadoDistribuicaoAtacado existente foi removida.';
    END

    -- Cria a tabela que armazenará a saída do cálculo
    CREATE TABLE dbo.RESULTADO_DISTRIBUICAO_ATACADO (
        PEDIDO NVARCHAR(100),
        CLIENTE NVARCHAR(255),
        ID_PRODUTO NVARCHAR(50),
        PRODUTO NVARCHAR(10),
        COR_PRODUTO NVARCHAR(100),
        ITEM_PEDIDO NVARCHAR(10),
        ENTREGA DATETIME,
        COORDENADO NVARCHAR(100),
        PRIORIDADE SMALLINT,
        TOTAL_ORIGINAL DECIMAL(18, 2),
        NEC_P1 INT,
        NEC_P2 INT,
        NEC_P3 INT,
        NEC_P4 INT,
        NEC_P5 INT,
        NEC_P6 INT,
        TOTAL_NECESSIDADE INT,
        ALOC_P1 INT,
        ALOC_P2 INT,
        ALOC_P3 INT,
        ALOC_P4 INT,
        ALOC_P5 INT,
        ALOC_P6 INT,
        TOTAL_ALOCADO INT,
        PRECO DECIMAL(10, 2),
        RESTANTE_P1 INT,
        RESTANTE_P2 INT,
        RESTANTE_P3 INT,
        RESTANTE_P4 INT,
        RESTANTE_P5 INT,
        RESTANTE_P6 INT,
        TOTAL_NAO_ATENDIDO INT,
        DATA_ATUALIZACAO DATETIME DEFAULT GETDATE()
    );
    PRINT 'Tabela dbo.RESULTADO_DISTRIBUICAO_ATACADO criada com sucesso.';

    -- 2. PREPARAÇÃO: Carregar os dados de origem em tabelas temporárias

    -- Tabela temporária para os pedidos
    IF OBJECT_ID('tempdb..#Pedidos') IS NOT NULL DROP TABLE #Pedidos;
    SELECT S.*, V.TOTAL_ORIGINAL INTO #Pedidos FROM [Cliente386_ERP].[dbo].[W_DRESS_WMS_ATACADO_SALDO_PEDIDO_ENTREGAR] AS S JOIN (SELECT CLIENTE_ATACADO, SUM(TOT_VALOR_ORIGINAL) AS TOTAL_ORIGINAL FROM VENDAS WHERE COLECAO IN (64, 65) AND TIPO = 'VENDA' GROUP BY CLIENTE_ATACADO) AS V ON S.NOME_CLIFOR = V.CLIENTE_ATACADO JOIN [Cliente386_ERP].[dbo].[PRODUTOS] AS P ON S.PRODUTO = P.PRODUTO
        WHERE S.COLECAO IN ('64', '65') AND S.APROVACAO = 'A' AND S.TIPO_CLIENTE IN ('MULTIMARCAS', 'REPRESENTANTE') AND S.FILIAL = 'ATACADO' AND S.TIPO_VENDA = 'VENDA';

    -- Tabela temporária para o estoque, que será atualizada durante o processo
    IF OBJECT_ID('tempdb..#EstoqueTemp') IS NOT NULL DROP TABLE #EstoqueTemp;
    SELECT * INTO #EstoqueTemp FROM [Cliente386_ERP].[dbo].[W_ESTOQUE_LIQUIDO_ATACADO] WHERE FILIAL = 'ATACADO' AND COLECAO IN (19, 64, 65);

    -- 3. DECLARAÇÃO DO CURSOR E VARIÁVEIS
    -- O CURSOR vai iterar sobre cada pedido, em ordem de prioridade, simulando o loop do Python.

    -- Variáveis para os dados do pedido atual
    DECLARE @Pedido NVARCHAR(100), @NomeCliente NVARCHAR(255), @IdProduto NVARCHAR(50), @Produto NVARCHAR(10), @CorProduto NVARCHAR(100), @ItemPedido NVARCHAR(10), @Entrega DATETIME, @Coordenado NVARCHAR(100), @Prioridade INT, @TotalOriginal DECIMAL(18,2), @Preco DECIMAL(10,2);
    DECLARE @VE1 INT, @VE2 INT, @VE3 INT, @VE4 INT, @VE5 INT, @VE6 INT;
    -- Variáveis para o estoque disponível do produto atual
    DECLARE @EstoqueD1 INT, @EstoqueD2 INT, @EstoqueD3 INT, @EstoqueD4 INT, @EstoqueD5 INT, @EstoqueD6 INT;

    -- Variáveis para o cálculo da alocação
    DECLARE @AlocadoP1 INT, @AlocadoP2 INT, @AlocadoP3 INT, @AlocadoP4 INT, @AlocadoP5 INT, @AlocadoP6 INT;

    -- << LINHA CORRIGIDA >>
    DECLARE pedidos_cursor CURSOR FOR
    SELECT PEDIDO, NOME_CLIFOR, ID_PRODUTO, PRODUTO, COR_PRODUTO, ITEM_PEDIDO, ENTREGA, COORDENADO, ISNULL(PRIORIDADE, 5), TOTAL_ORIGINAL, PRECO1, ISNULL(VE1,0), ISNULL(VE2,0), ISNULL(VE3,0), ISNULL(VE4,0), ISNULL(VE5,0), ISNULL(VE6,0)
    FROM #Pedidos
    ORDER BY ISNULL(PRIORIDADE, 5) ASC, NOME_CLIFOR, TOTAL_ORIGINAL DESC;

    -- 4. PROCESSAMENTO (LOOP DO CURSOR)
    BEGIN TRY
        PRINT 'Iniciando o cálculo de distribuição em T-SQL...';

        OPEN pedidos_cursor;
        FETCH NEXT FROM pedidos_cursor INTO @Pedido, @NomeCliente, @IdProduto, @Produto, @CorProduto, @ItemPedido, @Entrega, @Coordenado, @Prioridade, @TotalOriginal, @Preco, @VE1, @VE2, @VE3, @VE4, @VE5, @VE6;

        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Zera o estoque para este loop, caso o produto não exista na tabela de estoque
            SELECT @EstoqueD1=0, @EstoqueD2=0, @EstoqueD3=0, @EstoqueD4=0, @EstoqueD5=0, @EstoqueD6=0;

            -- Busca o estoque atualizado da tabela temporária para o produto do pedido atual
            SELECT
                @EstoqueD1 = ISNULL(D1, 0), @EstoqueD2 = ISNULL(D2, 0), @EstoqueD3 = ISNULL(D3, 0),
                @EstoqueD4 = ISNULL(D4, 0), @EstoqueD5 = ISNULL(D5, 0), @EstoqueD6 = ISNULL(D6, 0)
            FROM #EstoqueTemp
            WHERE ID_PRODUTO = @IdProduto;

            -- Lógica de alocação (o menor valor entre a necessidade e a disponibilidade)
            SET @AlocadoP1 = CASE WHEN @VE1 < @EstoqueD1 THEN @VE1 ELSE @EstoqueD1 END;
            SET @AlocadoP2 = CASE WHEN @VE2 < @EstoqueD2 THEN @VE2 ELSE @EstoqueD2 END;
            SET @AlocadoP3 = CASE WHEN @VE3 < @EstoqueD3 THEN @VE3 ELSE @EstoqueD3 END;
            SET @AlocadoP4 = CASE WHEN @VE4 < @EstoqueD4 THEN @VE4 ELSE @EstoqueD4 END;
            SET @AlocadoP5 = CASE WHEN @VE5 < @EstoqueD5 THEN @VE5 ELSE @EstoqueD5 END;
            SET @AlocadoP6 = CASE WHEN @VE6 < @EstoqueD6 THEN @VE6 ELSE @EstoqueD6 END;

            -- Se houve alguma alocação, atualiza o estoque na tabela temporária para o próximo pedido
            IF (@AlocadoP1 + @AlocadoP2 + @AlocadoP3 + @AlocadoP4 + @AlocadoP5 + @AlocadoP6) > 0
            BEGIN
                UPDATE #EstoqueTemp
                SET
                    D1 = D1 - @AlocadoP1, D2 = D2 - @AlocadoP2, D3 = D3 - @AlocadoP3,
                    D4 = D4 - @AlocadoP4, D5 = D5 - @AlocadoP5, D6 = D6 - @AlocadoP6
                WHERE ID_PRODUTO = @IdProduto;
            END

            -- Insere o resultado calculado na tabela permanente
            INSERT INTO dbo.RESULTADO_DISTRIBUICAO_ATACADO (
                PEDIDO, CLIENTE, ID_PRODUTO, PRODUTO, COR_PRODUTO, ITEM_PEDIDO, ENTREGA, COORDENADO, PRIORIDADE, TOTAL_ORIGINAL,
                NEC_P1, NEC_P2, NEC_P3, NEC_P4, NEC_P5, NEC_P6, TOTAL_NECESSIDADE,
                ALOC_P1, ALOC_P2, ALOC_P3, ALOC_P4, ALOC_P5, ALOC_P6, TOTAL_ALOCADO,
                PRECO,
                RESTANTE_P1, RESTANTE_P2, RESTANTE_P3, RESTANTE_P4, RESTANTE_P5, RESTANTE_P6, TOTAL_NAO_ATENDIDO
            )
            VALUES (
                @Pedido, @NomeCliente, @IdProduto, @Produto, @CorProduto, @ItemPedido, @Entrega, @Coordenado, ISNULL(@Prioridade, 5), @TotalOriginal,
                @VE1, @VE2, @VE3, @VE4, @VE5, @VE6, (@VE1 + @VE2 + @VE3 + @VE4 + @VE5 + @VE6),
                @AlocadoP1, @AlocadoP2, @AlocadoP3, @AlocadoP4, @AlocadoP5, @AlocadoP6, (@AlocadoP1 + @AlocadoP2 + @AlocadoP3 + @AlocadoP4 + @AlocadoP5 + @AlocadoP6),
                ISNULL(@Preco, 0),
                (@VE1 - @AlocadoP1), (@VE2 - @AlocadoP2), (@VE3 - @AlocadoP3), (@VE4 - @AlocadoP4), (@VE5 - @AlocadoP5), (@VE6 - @AlocadoP6),
                (@VE1 - @AlocadoP1) + (@VE2 - @AlocadoP2) + (@VE3 - @AlocadoP3) + (@VE4 - @AlocadoP4) + (@VE5 - @AlocadoP5) + (@VE6 - @AlocadoP6)
            );

            -- Pega o próximo pedido da lista
            FETCH NEXT FROM pedidos_cursor INTO @Pedido, @NomeCliente, @IdProduto, @Produto, @CorProduto, @ItemPedido, @Entrega, @Coordenado, @Prioridade, @TotalOriginal, @Preco, @VE1, @VE2, @VE3, @VE4, @VE5, @VE6;
        END

        -- Fecha e libera o cursor da memória
        CLOSE pedidos_cursor;
        DEALLOCATE pedidos_cursor;

        PRINT 'Procedure T-SQL executada e dados inseridos em dbo.ResultadoDistribuicaoAtacado com sucesso.';

    END TRY
    BEGIN CATCH
        -- Em caso de erro, garante que o cursor seja fechado se ainda estiver aberto
        IF CURSOR_STATUS('global', 'pedidos_cursor') >= 0
        BEGIN
            CLOSE pedidos_cursor;
            DEALLOCATE pedidos_cursor;
        END
        PRINT 'Procedure T-SQL: Erro ao executar o cálculo.';
        THROW;
    END CATCH

    -- Limpa as tabelas temporárias
    DROP TABLE #Pedidos;
    DROP TABLE #EstoqueTemp;

    SET NOCOUNT OFF;
END;
