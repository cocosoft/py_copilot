"""数据校验模型"""
from app.schemas.auth import UserRegister, UserLogin, UserResponse, Token, TokenPayload
from app.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse, ConversationListResponse, MessageCreate, MessageResponse, MessageListResponse
# LLM schemas will be imported as needed
from app.schemas.model_category import (
    ModelCategoryBase, ModelCategoryCreate, ModelCategoryUpdate,
    ModelCategoryResponse, ModelCategoryWithChildrenResponse,
    ModelCategoryListResponse, ModelCategoryAssociationCreate,
    ModelCategoryAssociationResponse, ModelWithCategoriesResponse,
    CategoryWithModelsResponse
)
from app.schemas.model_capability import (
    ModelCapabilityBase, ModelCapabilityCreate, ModelCapabilityUpdate,
    ModelCapabilityResponse, ModelCapabilityListResponse,
    ModelCapabilityAssociationCreate, ModelCapabilityAssociationUpdate,
    ModelCapabilityAssociationResponse, ModelWithCapabilitiesResponse,
    CapabilityWithModelsResponse
)
from app.schemas.model_management import ModelSupplierBase, ModelSupplierCreate, ModelSupplierUpdate, ModelSupplierResponse, ModelSupplierListResponse, ModelBase, ModelCreate, ModelUpdate, ModelResponse, ModelListResponse, ModelWithSupplierResponse

__all__ = [
    # Auth
    "UserRegister", "UserLogin", "UserResponse", "Token", "TokenPayload",
    # Conversation
    "ConversationCreate", "ConversationUpdate", "ConversationResponse", "ConversationListResponse", "MessageCreate", "MessageResponse", "MessageListResponse",
    # LLM

    # Model Category
    "ModelCategoryBase", "ModelCategoryCreate", "ModelCategoryUpdate", "ModelCategoryResponse", "ModelCategoryWithChildrenResponse", "ModelCategoryListResponse", "ModelCategoryAssociationCreate", "ModelCategoryAssociationResponse", "ModelWithCategoriesResponse", "CategoryWithModelsResponse",
    # Model Capability
    "ModelCapabilityBase", "ModelCapabilityCreate", "ModelCapabilityUpdate", "ModelCapabilityResponse", "ModelCapabilityListResponse", "ModelCapabilityAssociationCreate", "ModelCapabilityAssociationUpdate", "ModelCapabilityAssociationResponse", "ModelWithCapabilitiesResponse", "CapabilityWithModelsResponse",
    # Model Management
    "ModelSupplierBase", "ModelSupplierCreate", "ModelSupplierUpdate", "ModelSupplierResponse", "ModelSupplierListResponse", "ModelBase", "ModelCreate", "ModelUpdate", "ModelResponse", "ModelListResponse", "ModelWithSupplierResponse", "SetDefaultModelRequest",
    # Model Parameter
    "ModelParameterBase", "ModelParameterCreate", "ModelParameterUpdate", "ModelParameterResponse", "ModelParameterListResponse",
]