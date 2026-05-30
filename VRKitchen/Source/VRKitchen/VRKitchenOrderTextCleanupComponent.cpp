#include "VRKitchenOrderTextCleanupComponent.h"

#include "GameFramework/Actor.h"
#include "UObject/UnrealType.h"

namespace
{
	bool TrimTrailingIngredientSeparator(FString& Text)
	{
		const FString Original = Text;
		Text.TrimEndInline();
		while (Text.EndsWith(TEXT(",")))
		{
			Text.LeftChopInline(1);
			Text.TrimEndInline();
		}
		return Text != Original;
	}
}

UVRKitchenOrderTextCleanupComponent::UVRKitchenOrderTextCleanupComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
	PrimaryComponentTick.TickInterval = 0.1f;
}

void UVRKitchenOrderTextCleanupComponent::BeginPlay()
{
	Super::BeginPlay();
	CleanupTempIngredientsText();
}

void UVRKitchenOrderTextCleanupComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	CleanupTempIngredientsText();
}

void UVRKitchenOrderTextCleanupComponent::CleanupTempIngredientsText() const
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	if (FStrProperty* StringProperty = FindFProperty<FStrProperty>(Owner->GetClass(), TEXT("TempIngredientsText")))
	{
		FString Value = StringProperty->GetPropertyValue_InContainer(Owner);
		if (TrimTrailingIngredientSeparator(Value))
		{
			StringProperty->SetPropertyValue_InContainer(Owner, Value);
		}
		return;
	}

	if (FTextProperty* TextProperty = FindFProperty<FTextProperty>(Owner->GetClass(), TEXT("TempIngredientsText")))
	{
		FString Value = TextProperty->GetPropertyValue_InContainer(Owner).ToString();
		if (TrimTrailingIngredientSeparator(Value))
		{
			TextProperty->SetPropertyValue_InContainer(Owner, FText::FromString(Value));
		}
	}
}
