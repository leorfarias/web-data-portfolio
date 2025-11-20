Sub ExecutarProcedure_e_AtualizarTabela_EmB5()

    ' 1. Declaração de Variáveis
    Dim objConexao As Object   ' ADODB.Connection
    Dim objComando As Object   ' ADODB.Command
    Dim objRecordset As Object ' ADODB.Recordset
    Dim ws As Worksheet
    Dim tbl As ListObject
    Dim tblRange As Range
    Dim strConexao As String
    Dim strServidor As String, strBanco As String
    Dim nomeTabela As String
    
    nomeTabela = "DadosDistribuicao" ' Defina um nome fixo para sua tabela

    ' -- Defina a planilha de destino --
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Planilha1") ' Pode alterar o nome da aba aqui
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Sheets.Add
        ws.Name = "Planilha1"
    End If
    On Error GoTo 0

    ' -- Informações do seu servidor e banco de dados --
    strServidor = "DTKSRV05-VM"
    strBanco = "Cliente386_ERP"

    ' -- String de Conexão --
    strConexao = "Provider=SQLOLEDB;Data Source=" & strServidor & ";Initial Catalog=" & strBanco & ";Integrated Security=SSPI;"

    ' -- Criar Objetos --
    Set objConexao = CreateObject("ADODB.Connection")
    Set objComando = CreateObject("ADODB.Command")
    Set objRecordset = CreateObject("ADODB.Recordset")

    On Error GoTo TratamentoErro

    ' -- Abrir a Conexão --
    objConexao.Open strConexao
    Set objComando.ActiveConnection = objConexao

    '======================================================================
    '== ETAPA 1: Executar a Stored Procedure de ação ======================
    '======================================================================
    With objComando
        .CommandText = "sp_distribuicao_exportacao" ' Nome da sua procedure
        .CommandType = 4 ' adCmdStoredProc
        .CommandTimeout = 120
    End With
    
    objComando.Execute
    
    '======================================================================
    '== ETAPA 2: Chamar a View para obter os dados ========================
    '======================================================================
    
    objComando.CommandText = "SELECT * FROM W_RESULTADO_DISTRIBUICAO_EXPORTACAO" ' << ALTERE O NOME DA SUA VIEW AQUI
    objComando.CommandType = 1 ' adCmdText
    
    Set objRecordset = objComando.Execute
    
    ' -- Processar os dados retornados pela View --
    If Not objRecordset.EOF Then
    
        ' Tenta encontrar a tabela existente
        On Error Resume Next
        Set tbl = ws.ListObjects(nomeTabela)
        On Error GoTo TratamentoErro

        If tbl Is Nothing Then
            ' A tabela não existe, então limpa a área e cria uma nova
            ws.Range("B5").CurrentRegion.Clear
            
            ' Coloca os cabeçalhos das colunas, começando em B5
            Dim i As Integer
            For i = 0 To objRecordset.Fields.Count - 1
                ws.Cells(5, i + 2).Value = objRecordset.Fields(i).Name
            Next i
            
            ' Cola os dados a partir da célula B6
            ws.Range("B6").CopyFromRecordset objRecordset
            
            ' Cria a tabela pela primeira vez
            Set tbl = ws.ListObjects.Add(SourceType:=xlSrcRange, _
                                         Source:=ws.Range("B5").CurrentRegion, _
                                         XlListObjectHasHeaders:=xlYes)
            tbl.Name = nomeTabela
            tbl.TableStyle = "TableStyleMedium9"
            
        Else
            ' A tabela já existe, então apenas atualiza os dados
            
            ' Limpa apenas o corpo de dados da tabela, mantendo os cabeçalhos
            If Not tbl.DataBodyRange Is Nothing Then
                tbl.DataBodyRange.ClearContents
            End If
            
            ' Cola os novos dados na primeira célula do corpo da tabela (abaixo do cabeçalho)
            tbl.HeaderRowRange.Offset(1, 0).Cells(1, 1).CopyFromRecordset objRecordset
            
            ' Redimensiona a tabela para o novo conjunto de dados
            Set tblRange = ws.Range(tbl.HeaderRowRange.Cells(1, 1), _
                                    tbl.HeaderRowRange.Cells(1, 1).End(xlDown).End(xlToRight))
            tbl.Resize tblRange
        End If
        
        ws.Columns.AutoFit ' Ajusta a largura das colunas
        
        MsgBox "Ação executada e tabela de dados atualizada com sucesso!", vbInformation
    Else
        ' Se não retornou dados, apenas limpa a tabela existente
        On Error Resume Next
        Set tbl = ws.ListObjects(nomeTabela)
        If Not tbl Is Nothing Then
            If Not tbl.DataBodyRange Is Nothing Then
                tbl.DataBodyRange.ClearContents
            End If
        End If
        On Error GoTo TratamentoErro
        
        MsgBox "A procedure foi executada, mas a view não retornou dados. A tabela foi limpa.", vbInformation
    End If

TratamentoErro:
    ' -- Fechar e Limpar os Objetos --
    If Not objRecordset Is Nothing Then
        If objRecordset.State = 1 Then objRecordset.Close
        Set objRecordset = Nothing
    End If
    If Not objComando Is Nothing Then Set objComando = Nothing
    If Not objConexao Is Nothing Then
        If objConexao.State = 1 Then objConexao.Close
        Set objConexao = Nothing
    End If

    If Err.Number <> 0 Then
        MsgBox "Ocorreu um erro: " & Err.Description, vbCritical
    End If

End Sub