# Proposta: Camada de Abstração para Integração com Flows API

## Resumo Executivo

Este documento apresenta uma camada de abstração implementada no `agents-toolkit` para simplificar e padronizar a integração das Tools com a API do Flows.

---

## 1. Problema Atual

### Cenário Antes da Abstração

```mermaid
flowchart TB
    subgraph "Situacao Atual - Sem Abstracao"
        T1[Tool 1<br/>create_ticket.py] --> |HTTP Request Manual| F[Flows API]
        T2[Tool 2<br/>update_contact.py] --> |HTTP Request Manual| F
        T3[Tool 3<br/>send_broadcast.py] --> |HTTP Request Manual| F
        T4[Tool N<br/>...] --> |HTTP Request Manual| F
    end
    
    style T1 fill:#e74c3c,color:#fff
    style T2 fill:#e74c3c,color:#fff
    style T3 fill:#e74c3c,color:#fff
    style T4 fill:#e74c3c,color:#fff
    style F fill:#ecf0f1,color:#000
```

### Problemas Identificados

| Problema | Impacto |
|----------|---------|
| **Código duplicado** | Cada tool reimplementa lógica de autenticação e requests |
| **Inconsistência** | Diferentes tratamentos de erro entre tools |
| **Manutenção difícil** | Mudanças na API do Flows requerem alterações em múltiplas tools |
| **Curva de aprendizado** | Desenvolvedores precisam entender detalhes da API do Flows |
| **Bugs recorrentes** | Mesmos erros se repetem em diferentes implementações |

---

## 2. Solução Proposta

### Arquitetura com Camada de Abstração

```mermaid
flowchart TB
    subgraph "Nova Arquitetura - Com Abstracao"
        subgraph "Tools Layer"
            T1[Tool 1]
            T2[Tool 2]
            T3[Tool 3]
            T4[Tool N]
        end
        
        subgraph "Abstraction Layer"
            FC[FlowsClient]
            
            subgraph "Resources"
                CR[ContactsResource]
                TR[TicketsResource]
                BR[BroadcastsResource]
                FR[FlowsResource]
                MR[MessagesResource]
                CHR[ChannelsResource]
            end
            
            BASE[BaseResource<br/>HTTP + Error Handling]
        end
        
        T1 --> FC
        T2 --> FC
        T3 --> FC
        T4 --> FC
        
        FC --> CR
        FC --> TR
        FC --> BR
        FC --> FR
        FC --> MR
        FC --> CHR
        
        CR --> BASE
        TR --> BASE
        BR --> BASE
        FR --> BASE
        MR --> BASE
        CHR --> BASE
        
        BASE --> |"JWT Auth"| FLOWS[Flows API]
    end
    
    style FC fill:#1abc9c,color:#000
    style BASE fill:#3498db,color:#fff
    style FLOWS fill:#2ecc71,color:#000
    style T1 fill:#ecf0f1,color:#000
    style T2 fill:#ecf0f1,color:#000
    style T3 fill:#ecf0f1,color:#000
    style T4 fill:#ecf0f1,color:#000
    style CR fill:#f1c40f,color:#000
    style TR fill:#f1c40f,color:#000
    style BR fill:#f1c40f,color:#000
    style FR fill:#f1c40f,color:#000
    style MR fill:#f1c40f,color:#000
    style CHR fill:#f1c40f,color:#000
```

---

## 3. Fluxo de Autenticação JWT

### Como o JWT é utilizado

```mermaid
sequenceDiagram
    autonumber
    participant Nexus
    participant Lambda as Lambda (weni-cli-backend)
    participant Tool as Tool (agents-toolkit)
    participant Client as FlowsClient
    participant Flows as Flows API

    Nexus->>Lambda: Envia JWT com project_uuid no payload
    Lambda->>Lambda: Monta Context com JWT
    Lambda->>Tool: Executa Tool com Context
    Tool->>Client: FlowsClient.from_context(context)
    Client->>Client: Extrai flows_jwt do Context
    
    Tool->>Client: flows.tickets.contact_has_open(urn)
    Client->>Flows: GET /api/v2/internals/contact_has_open_ticket<br/>Authorization: Bearer {jwt}
    
    Flows->>Flows: Decodifica JWT
    Note over Flows: Extrai project_uuid<br/>do payload do JWT
    Flows->>Flows: Valida acesso ao projeto
    
    Flows-->>Client: Response
    Client-->>Tool: Resultado tipado
```

### Estrutura do JWT

```mermaid
flowchart LR
    subgraph "JWT Token"
        direction TB
        H[Header<br/>alg: RS256]
        P[Payload<br/>project_uuid: uuid<br/>email: user@example.com<br/>exp: timestamp]
        S[Signature]
    end
    
    H --> P --> S
    
    style H fill:#ecf0f1,color:#000
    style P fill:#f1c40f,color:#000
    style S fill:#ecf0f1,color:#000
```

**Importante:** O `project_uuid` está **dentro do JWT**, não é passado como parâmetro. O Flows extrai automaticamente.

---

## 4. Arquitetura de Componentes

### Estrutura do Módulo

```mermaid
classDiagram
    class FlowsClient {
        +base_url: str
        +jwt_token: str
        +contacts: ContactsResource
        +tickets: TicketsResource
        +broadcasts: BroadcastsResource
        +flows: FlowsResource
        +messages: MessagesResource
        +channels: ChannelsResource
        +from_context(context) FlowsClient$
    }
    
    class BaseResource {
        -_client: FlowsClient
        -_headers: dict
        +_get(path, params)
        +_post(path, json_data)
        +_patch(path, json_data)
        +_delete(path)
        -_handle_response(response)
    }
    
    class ContactsResource {
        +list_fields()
        +create_field(name, value_type)
        +update_fields(contact_urn, fields)
        +list_groups()
    }
    
    class TicketsResource {
        +contact_has_open(contact_urn)
        +open(contact_urn, topic_uuid, body)
        +get_departments()
        +get_queues()
    }
    
    class BroadcastsResource {
        +send(text, contact_uuids)
        +send_whatsapp(template_name, template_uuid)
        +get_statistics()
    }
    
    FlowsClient --> ContactsResource
    FlowsClient --> TicketsResource
    FlowsClient --> BroadcastsResource
    
    ContactsResource --|> BaseResource
    TicketsResource --|> BaseResource
    BroadcastsResource --|> BaseResource
```

---

## 5. Fluxo de Execução de uma Tool

### Exemplo: Tool que verifica ticket e atualiza contato

```mermaid
flowchart TB
    subgraph "1. Inicializacao"
        A[Lambda recebe evento<br/>com JWT do Nexus] --> B[Monta Context<br/>com flows_jwt]
        B --> C[Executa Tool]
    end
    
    subgraph "2. Tool Execution"
        C --> D[FlowsClient.from_context]
        D --> E{Verificar ticket aberto?}
        
        E -->|Sim| F[flows.tickets.contact_has_open]
        F --> G{Tem ticket?}
        
        G -->|Nao| H[flows.tickets.open]
        H --> I[flows.contacts.update_fields]
        
        G -->|Sim| J[Retorna mensagem<br/>ticket existente]
        
        I --> K[Retorna sucesso]
    end
    
    subgraph "3. Flows API Calls"
        F -.->|JWT Auth| API1[GET /contact_has_open_ticket]
        H -.->|JWT Auth| API2[POST /open_ticket]
        I -.->|JWT Auth| API3[PATCH /update_contacts_fields]
    end
    
    style D fill:#1abc9c,color:#000
    style API1 fill:#2ecc71,color:#000
    style API2 fill:#2ecc71,color:#000
    style API3 fill:#2ecc71,color:#000
    style A fill:#ecf0f1,color:#000
    style B fill:#ecf0f1,color:#000
    style C fill:#ecf0f1,color:#000
    style K fill:#27ae60,color:#fff
    style J fill:#f39c12,color:#000
```

---

## 6. Tratamento de Erros

### Hierarquia de Exceções

```mermaid
flowchart TB
    E[FlowsAPIError] --> E1[FlowsAuthenticationError<br/>401/403]
    E --> E2[FlowsNotFoundError<br/>404]
    E --> E3[FlowsValidationError<br/>400]
    E --> E4[FlowsServerError<br/>5xx]
    
    CFG[FlowsConfigurationError] 
    
    style E fill:#e74c3c,color:#fff
    style E1 fill:#f39c12,color:#000
    style E2 fill:#f39c12,color:#000
    style E3 fill:#f39c12,color:#000
    style E4 fill:#f39c12,color:#000
    style CFG fill:#9b59b6,color:#fff
```

### Fluxo de Error Handling

```mermaid
sequenceDiagram
    participant Tool
    participant Client as FlowsClient
    participant Base as BaseResource
    participant Flows as Flows API

    Tool->>Client: flows.contacts.update_fields(...)
    Client->>Base: _patch(path, data)
    Base->>Flows: PATCH request
    
    alt Success (2xx)
        Flows-->>Base: 200 OK
        Base-->>Client: parsed data
        Client-->>Tool: dict result
    else Validation Error (400)
        Flows-->>Base: 400 Bad Request
        Base->>Base: raise FlowsValidationError
        Base-->>Tool: FlowsValidationError
    else Auth Error (401/403)
        Flows-->>Base: 401 Unauthorized
        Base->>Base: raise FlowsAuthenticationError
        Base-->>Tool: FlowsAuthenticationError
    else Not Found (404)
        Flows-->>Base: 404 Not Found
        Base->>Base: raise FlowsNotFoundError
        Base-->>Tool: FlowsNotFoundError
    end
```

---

## 7. Comparação: Antes vs Depois

### Código ANTES (sem abstração)

```python
import requests
import json

class CreateTicketTool(Tool):
    def execute(self, context: Context):
        # Extrair JWT manualmente
        jwt = context.credentials.get("jwt")
        flows_url = context.credentials.get("flows_url")
        
        # Construir headers manualmente
        headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json"
        }
        
        # Verificar ticket existente
        response = requests.get(
            f"{flows_url}/api/v2/internals/contact_has_open_ticket",
            headers=headers,
            params={"contact_urn": context.contact.get("urn")}
        )
        
        # Tratamento de erro manual
        if response.status_code != 200:
            return {"error": "Failed to check ticket"}
        
        data = response.json()
        if data.get("has_open_ticket"):
            return {"message": "Already has ticket"}
        
        # Abrir ticket
        response = requests.post(
            f"{flows_url}/api/v2/internals/open_ticket",
            headers=headers,
            json={
                "contact_urn": context.contact.get("urn"),
                "body": "Customer needs help"
            }
        )
        
        # Mais tratamento de erro...
        if response.status_code != 201:
            return {"error": "Failed to open ticket"}
        
        return {"success": True}
```

### Código DEPOIS (com abstração)

```python
from weni.flows import FlowsClient

class CreateTicketTool(Tool):
    def execute(self, context: Context):
        flows = FlowsClient.from_context(context)
        contact_urn = context.contact.get("urn")
        
        # Verificar ticket existente
        if flows.tickets.contact_has_open(contact_urn):
            return {"message": "Already has ticket"}
        
        # Abrir ticket
        ticket = flows.tickets.open(
            contact_urn=contact_urn,
            body="Customer needs help"
        )
        
        return {"success": True, "ticket_id": ticket.get("uuid")}
```

### Métricas de Melhoria

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Linhas de código | ~45 | ~15 | **-67%** |
| Imports necessários | 3 | 1 | **-67%** |
| Pontos de erro manual | 4+ | 0 | **-100%** |
| Tempo de desenvolvimento | ~2h | ~20min | **-83%** |

---

## 8. Repositórios Envolvidos

```mermaid
flowchart LR
    subgraph "Ecossistema"
        AT[agents-toolkit<br/>SDK + FlowsClient]
        CB[weni-cli-backend<br/>Lambdas]
        FL[flows<br/>API]
        NX[nexus<br/>Auth + JWT]
    end
    
    NX -->|JWT com project_uuid| CB
    CB -->|Executa Tools| AT
    AT -->|HTTP + JWT| FL
    
    style AT fill:#1abc9c,color:#000
    style CB fill:#3498db,color:#fff
    style FL fill:#2ecc71,color:#000
    style NX fill:#ecf0f1,color:#000
```

---

## 9. Endpoints Suportados

### Resources e Métodos Disponíveis

| Resource | Métodos |
|----------|---------|
| **contacts** | `list_fields`, `create_field`, `update_fields`, `list_groups`, `create_group_from_broadcast`, `get_group_fields`, `export_by_broadcast_status` |
| **tickets** | `contact_has_open`, `open`, `get_assignee`, `get_departments`, `get_queues` |
| **broadcasts** | `send`, `send_whatsapp`, `get_statistics`, `get_groups_stats`, `get_monthly_stats` |
| **flows** | `start`, `import_definition` |
| **messages** | `send` |
| **channels** | `create` |

---

## 10. Próximos Passos

### Roadmap de Implementação

```mermaid
gantt
    title Roadmap de Implementacao
    dateFormat  YYYY-MM-DD
    section Fase 1 - Core
    Implementar FlowsClient           :done, f1, 2026-01-23, 1d
    Implementar Resources             :done, f2, after f1, 1d
    Testes unitarios                  :done, f3, after f2, 1d
    
    section Fase 2 - Integracao
    Ajustar weni-cli-backend          :f4, after f3, 2d
    Passar JWT no Context             :f5, after f4, 1d
    
    section Fase 3 - Migracao
    Migrar tools existentes           :f6, after f5, 5d
    Documentacao                      :f7, after f5, 2d
    
    section Fase 4 - Expansao
    Adicionar novos endpoints         :f8, after f6, 3d
    Monitoramento e metricas          :f9, after f8, 2d
```

---

## 11. Benefícios Consolidados

### Resumo de Benefícios

| Benefício | Descrição |
|-----------|-----------|
| 🔄 **DRY** | Código de integração escrito uma vez, usado em todas as tools |
| 🛡️ **Segurança** | Autenticação JWT centralizada e consistente |
| 🐛 **Debugging** | Erros tipados facilitam identificação de problemas |
| 📚 **Documentação** | API clara e auto-documentada |
| 🧪 **Testabilidade** | Resources facilmente mockáveis |
| ⚡ **Produtividade** | Desenvolvedores focam na lógica de negócio |

### Matriz de Impacto

| Benefício | Esforço | Impacto |
|-----------|---------|---------|
| Redução de código | Baixo | **Alto** |
| Padronização | Baixo | **Alto** |
| Manutenibilidade | Baixo | **Alto** |
| Onboarding devs | Médio | Alto |
| Error handling | Baixo | **Alto** |
| Testabilidade | Médio | Alto |

---

## 12. Conclusão

A camada de abstração `FlowsClient` no `agents-toolkit` resolve problemas críticos de duplicação de código, inconsistência e manutenibilidade, proporcionando uma interface limpa e ergonômica para integração com a API do Flows.

**Recomendação:** Aprovar a implementação e iniciar a migração gradual das tools existentes.

---

*Documento gerado em: Janeiro 2026*  
*Versão: 1.0*
