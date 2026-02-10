# Tracing Module

O módulo `tracing` fornece capacidades de rastreamento de execução para agentes ativos (Tools) e passivos (PreProcessors, Rules, etc.).

## Características

- ✅ Rastreamento automático de métodos com decorator `@trace()`
- ✅ Captura de entrada, saída, duração e erros
- ✅ Funciona com Tools (agentes ativos) e PreProcessors (agentes passivos)
- ✅ Injeção automática de trace em dados de resposta
- ✅ Nomenclatura genérica (`TracedAgent`) para suportar ambos os tipos

## Uso Básico

### Com Tool (Agente Ativo)

```python
from weni import Tool
from weni.tracing import TracedAgent, trace
from weni.context import Context
from weni.responses import TextResponse, ResponseObject

class MinhaTool(TracedAgent, Tool):
    def execute(self, context: Context) -> ResponseObject:
        # Processar dados
        resultado = self._processar_dados(context)
        
        # Criar resposta
        data, format = TextResponse(data=resultado)
        
        # Injetar trace automaticamente
        data = self._inject_trace(data)
        
        return data, format

    @trace()
    def _processar_dados(self, context: Context) -> dict:
        # Sua lógica aqui
        return {"resultado": "sucesso", "valor": 42}
```

### Com PreProcessor (Agente Passivo)

```python
from weni.preprocessor import PreProcessor, ProcessedData
from weni.tracing import TracedAgent, trace
from weni.context.preprocessor_context import PreProcessorContext

class MeuPreProcessor(TracedAgent, PreProcessor):
    def process(self, context: PreProcessorContext) -> ProcessedData:
        # Validar dados
        dados_validados = self._validar(context)
        
        # Preparar dados
        data = {"dados": dados_validados}
        
        # Injetar trace automaticamente
        data = self._inject_trace(data)
        
        return ProcessedData("urn-exemplo", data)

    @trace()
    def _validar(self, context: PreProcessorContext) -> dict:
        # Sua lógica de validação aqui
        return context.payload
```

## Opções do Decorator `@trace()`

```python
@trace(capture_input=True, capture_output=True)  # Padrão: captura tudo
def meu_metodo(self, dados: dict) -> dict:
    return processar(dados)

@trace(capture_output=False)  # Não captura saída (dados sensíveis)
def autenticar(self, credenciais: dict) -> str:
    return token_secreto

@trace(capture_input=False)  # Não captura entrada
def processar_sensivel(self, senha: str) -> dict:
    return {"status": "ok"}
```

## Nome Personalizado do Agente

```python
class MinhaTool(TracedAgent, Tool):
    AGENT_NAME = "MeuAgenteCustomizado"  # Override do nome padrão
    
    @trace()
    def execute(self, context: Context) -> ResponseObject:
        # ...
```

## Estrutura do Trace

O trace injetado tem a seguinte estrutura:

```python
{
    "_execution_trace": {
        "agent_name": "NomeDoAgente",
        "started_at": "2024-01-01T12:00:00.000Z",
        "completed_at": "2024-01-01T12:00:01.500Z",
        "total_duration_ms": 1500.0,
        "status": "completed",  # ou "failed"
        "total_steps": 2,
        "steps": [
            {
                "order": 1,
                "class": "MinhaTool",
                "method": "_processar_dados",
                "status": "ok",  # ou "failed"
                "input": {...},
                "output": {...},
                "duration_ms": 100.5
            }
        ],
        "error_summary": "..."  # Apenas se houver erro
    }
}
```

## Compatibilidade com Versões Anteriores

Para manter compatibilidade, os seguintes aliases estão disponíveis:

```python
from weni.tracing import TracedProcessor  # Alias para TracedAgent
from weni.tracing import ExecutionTracerMixin  # Alias para TracedAgent
```

## Reset do Tracer

Para resetar o tracer entre execuções:

```python
tool._reset_tracer()
```

## Exemplos Avançados

### Múltiplos Métodos Rastreados

```python
class ToolComplexa(TracedAgent, Tool):
    def execute(self, context: Context) -> ResponseObject:
        dados = self._extrair_dados(context)
        validados = self._validar(dados)
        processados = self._processar(validados)
        
        data, format = TextResponse(data=processados)
        return self._inject_trace(data), format

    @trace()
    def _extrair_dados(self, context: Context) -> dict:
        return context.parameters

    @trace()
    def _validar(self, dados: dict) -> dict:
        # Validação
        return dados

    @trace()
    def _processar(self, dados: dict) -> dict:
        # Processamento
        return {"resultado": dados}
```

### Tratamento de Erros

```python
class ToolComErro(TracedAgent, Tool):
    @trace()
    def _metodo_com_erro(self):
        raise ValueError("Erro de teste")
        # O trace captura automaticamente o erro
```

O trace incluirá:
- Status: "failed"
- error_summary: "ValueError: Erro de teste"
- Step com status "failed" e detalhes do erro
