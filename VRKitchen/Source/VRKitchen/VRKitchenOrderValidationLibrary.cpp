#include "VRKitchenOrderValidationLibrary.h"

#include "Components/PrimitiveComponent.h"
#include "Components/SceneComponent.h"
#include "Components/TextRenderComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "UObject/UnrealType.h"

namespace
{
	const FName TagBottomBun(TEXT("Bottom_Bun"));
	const FName TagTopBun(TEXT("Top_Bun"));
	const FName TagCookedPatty(TEXT("Cooked_Patty"));
	const FName TagCookedMeat(TEXT("Cooked_Meat"));
	const FName TagChoppedLettuce(TEXT("Chopped_Lettuce"));
	const FName TagChoppedTomato(TEXT("Chopped_Tomato"));
	const FName TagRawPatty(TEXT("Raw_Patty"));
	const FName TagRawMeat(TEXT("Raw_Meat"));
	const FName TagRawLettuce(TEXT("Raw_Lettuce"));
	const FName TagRawTomato(TEXT("Raw_Tomato"));

	const TArray<FName>& KnownFoodTags()
	{
		static const TArray<FName> Tags = {
			TagBottomBun,
			TagCookedPatty,
			TagCookedMeat,
			TagChoppedLettuce,
			TagChoppedTomato,
			TagTopBun,
			TagRawPatty,
			TagRawMeat,
			TagRawLettuce,
			TagRawTomato,
		};
		return Tags;
	}

	template <typename TComponent>
	TComponent* FindComponentByName(AActor* Actor, const FName ComponentName)
	{
		if (!Actor)
		{
			return nullptr;
		}

		TArray<TComponent*> Components;
		Actor->GetComponents<TComponent>(Components);
		for (TComponent* Component : Components)
		{
			if (Component && Component->GetFName() == ComponentName)
			{
				return Component;
			}
		}
		return Components.Num() > 0 ? Components[0] : nullptr;
	}

	FName FindPrimaryFoodTag(const AActor* Actor)
	{
		if (!Actor)
		{
			return NAME_None;
		}

		for (const FName& Candidate : KnownFoodTags())
		{
			if (Actor->Tags.Contains(Candidate))
			{
				return Candidate;
			}
		}
		return NAME_None;
	}

	struct FSubmittedFood
	{
		TWeakObjectPtr<AActor> Actor;
		FName FoodTag = NAME_None;
		double SortZ = 0.0;
	};

	double GetSortZ(AActor* Actor, USceneComponent* StackCenter)
	{
		if (!Actor)
		{
			return 0.0;
		}

		if (StackCenter)
		{
			return StackCenter->GetComponentTransform().InverseTransformPosition(Actor->GetActorLocation()).Z;
		}

		return Actor->GetActorLocation().Z;
	}

	void AddSubmittedActor(AActor* Actor, USceneComponent* StackCenter, TSet<AActor*>& SeenActors, TArray<FSubmittedFood>& OutFoods, const bool bAllowUnknownTag)
	{
		if (!Actor || SeenActors.Contains(Actor))
		{
			return;
		}

		const FName FoodTag = FindPrimaryFoodTag(Actor);
		if (FoodTag.IsNone() && !bAllowUnknownTag)
		{
			return;
		}

		SeenActors.Add(Actor);

		FSubmittedFood Food;
		Food.Actor = Actor;
		Food.FoodTag = FoodTag;
		Food.SortZ = GetSortZ(Actor, StackCenter);
		OutFoods.Add(Food);
	}

	TArray<FSubmittedFood> GatherSubmittedFoods(AActor* DeliveryArea)
	{
		TArray<FSubmittedFood> Foods;
		if (!DeliveryArea)
		{
			return Foods;
		}

		USceneComponent* StackCenter = FindComponentByName<USceneComponent>(DeliveryArea, TEXT("StackCenter"));
		UPrimitiveComponent* Box = FindComponentByName<UPrimitiveComponent>(DeliveryArea, TEXT("Box"));
		TSet<AActor*> SeenActors;

		TArray<AActor*> AttachedActors;
		DeliveryArea->GetAttachedActors(AttachedActors, true, true);
		for (AActor* AttachedActor : AttachedActors)
		{
			AddSubmittedActor(AttachedActor, StackCenter, SeenActors, Foods, true);
		}

		if (UWorld* World = DeliveryArea->GetWorld())
		{
			for (TActorIterator<AActor> It(World); It; ++It)
			{
				AActor* Candidate = *It;
				if (!Candidate || Candidate == DeliveryArea)
				{
					continue;
				}

				bool bAttachedToDelivery = Candidate->GetAttachParentActor() == DeliveryArea;
				if (!bAttachedToDelivery && StackCenter)
				{
					if (USceneComponent* CandidateRoot = Candidate->GetRootComponent())
					{
						bAttachedToDelivery = CandidateRoot->GetAttachParent() == StackCenter;
					}
				}

				if (bAttachedToDelivery)
				{
					AddSubmittedActor(Candidate, StackCenter, SeenActors, Foods, true);
				}
			}
		}

		if (Foods.Num() == 0 && Box)
		{
			TArray<AActor*> OverlappingActors;
			Box->GetOverlappingActors(OverlappingActors);
			for (AActor* OverlappingActor : OverlappingActors)
			{
				if (OverlappingActor != DeliveryArea)
				{
					AddSubmittedActor(OverlappingActor, StackCenter, SeenActors, Foods, false);
				}
			}
		}

		Foods.Sort([](const FSubmittedFood& A, const FSubmittedFood& B)
		{
			return A.SortZ < B.SortZ;
		});

		return Foods;
	}

	bool GetCurrentOrderRequiredTags(AActor* OrderManager, TArray<FName>& OutRequiredTags)
	{
		OutRequiredTags.Reset();
		if (!OrderManager)
		{
			return false;
		}

		FStructProperty* CurrentOrderProperty = FindFProperty<FStructProperty>(OrderManager->GetClass(), TEXT("CurrentOrder"));
		if (!CurrentOrderProperty || !CurrentOrderProperty->Struct)
		{
			return false;
		}

		void* CurrentOrderPtr = CurrentOrderProperty->ContainerPtrToValuePtr<void>(OrderManager);
		if (!CurrentOrderPtr)
		{
			return false;
		}

		FArrayProperty* RequiredTagsProperty = nullptr;
		for (TFieldIterator<FProperty> It(CurrentOrderProperty->Struct); It; ++It)
		{
			if (It->GetName().StartsWith(TEXT("RequiredTags")))
			{
				RequiredTagsProperty = CastField<FArrayProperty>(*It);
				break;
			}
		}

		if (!RequiredTagsProperty)
		{
			return false;
		}

		FScriptArrayHelper ArrayHelper(RequiredTagsProperty, RequiredTagsProperty->ContainerPtrToValuePtr<void>(CurrentOrderPtr));
		for (int32 Index = 0; Index < ArrayHelper.Num(); ++Index)
		{
			void* ElementPtr = ArrayHelper.GetRawPtr(Index);
			if (FNameProperty* NameProperty = CastField<FNameProperty>(RequiredTagsProperty->Inner))
			{
				OutRequiredTags.Add(NameProperty->GetPropertyValue(ElementPtr));
			}
			else if (FStrProperty* StringProperty = CastField<FStrProperty>(RequiredTagsProperty->Inner))
			{
				OutRequiredTags.Add(FName(*StringProperty->GetPropertyValue(ElementPtr)));
			}
		}

		return OutRequiredTags.Num() > 0;
	}

	AActor* FindOrderManager(UWorld* World)
	{
		if (!World)
		{
			return nullptr;
		}

		static const TCHAR* OrderManagerClassPath = TEXT("/Game/_Project/Gameplay/Orders/BP_OrderManager_Playable.BP_OrderManager_Playable_C");
		UClass* OrderManagerClass = StaticLoadClass(AActor::StaticClass(), nullptr, OrderManagerClassPath);
		return OrderManagerClass ? UGameplayStatics::GetActorOfClass(World, OrderManagerClass) : nullptr;
	}

	bool SubmittedTagsMatchRequiredTags(const TArray<FSubmittedFood>& SubmittedFoods, const TArray<FName>& RequiredTags)
	{
		if (SubmittedFoods.Num() != RequiredTags.Num())
		{
			return false;
		}

		for (int32 Index = 0; Index < RequiredTags.Num(); ++Index)
		{
			if (SubmittedFoods[Index].FoodTag != RequiredTags[Index])
			{
				return false;
			}
		}

		return true;
	}

	void CallMakeClean(AActor* DeliveryArea)
	{
		if (!DeliveryArea)
		{
			return;
		}

		if (UFunction* MakeCleanFunction = DeliveryArea->FindFunction(TEXT("MakeClean")))
		{
			DeliveryArea->ProcessEvent(MakeCleanFunction, nullptr);
		}
	}

	void ResetCurrentZ(AActor* DeliveryArea)
	{
		if (!DeliveryArea)
		{
			return;
		}

		if (FDoubleProperty* CurrentZProperty = FindFProperty<FDoubleProperty>(DeliveryArea->GetClass(), TEXT("CurrentZ")))
		{
			CurrentZProperty->SetPropertyValue_InContainer(DeliveryArea, 0.0);
		}
		else if (FFloatProperty* CurrentZFloatProperty = FindFProperty<FFloatProperty>(DeliveryArea->GetClass(), TEXT("CurrentZ")))
		{
			CurrentZFloatProperty->SetPropertyValue_InContainer(DeliveryArea, 0.0f);
		}
	}

	void ClearSubmittedFoods(AActor* DeliveryArea, const TArray<FSubmittedFood>& SubmittedFoods)
	{
		for (const FSubmittedFood& SubmittedFood : SubmittedFoods)
		{
			if (AActor* FoodActor = SubmittedFood.Actor.Get())
			{
				FoodActor->Destroy();
			}
		}

		ResetCurrentZ(DeliveryArea);
		CallMakeClean(DeliveryArea);
	}

	void SpawnFloatingFeedback(AActor* Anchor, const TCHAR* Message, const FColor& Color)
	{
		if (!Anchor || !Anchor->GetWorld())
		{
			return;
		}

		USceneComponent* RootComponent = Anchor->GetRootComponent();
		UTextRenderComponent* TextComponent = NewObject<UTextRenderComponent>(Anchor);
		if (!TextComponent)
		{
			return;
		}

		TextComponent->SetText(FText::FromString(Message));
		TextComponent->SetTextRenderColor(Color);
		TextComponent->SetHorizontalAlignment(EHTA_Center);
		TextComponent->SetVerticalAlignment(EVRTA_TextCenter);
		TextComponent->SetWorldSize(24.0f);
		TextComponent->SetRelativeLocation(FVector(0.0f, 0.0f, 70.0f));
		if (RootComponent)
		{
			TextComponent->SetupAttachment(RootComponent);
		}
		TextComponent->RegisterComponent();

		TWeakObjectPtr<UTextRenderComponent> WeakTextComponent = TextComponent;
		FTimerHandle DestroyTimerHandle;
		Anchor->GetWorld()->GetTimerManager().SetTimer(
			DestroyTimerHandle,
			[WeakTextComponent]()
			{
				if (WeakTextComponent.IsValid())
				{
					WeakTextComponent->DestroyComponent();
				}
			},
			1.25f,
			false);
	}

	void CallStableAddScore(AActor* OrderManager)
	{
		if (!OrderManager)
		{
			return;
		}

		UFunction* StableAddScoreFunction = OrderManager->FindFunction(TEXT("StableAddScore"));
		if (!StableAddScoreFunction)
		{
			return;
		}

		uint8* Params = static_cast<uint8*>(FMemory_Alloca(StableAddScoreFunction->ParmsSize));
		FMemory::Memzero(Params, StableAddScoreFunction->ParmsSize);
		for (TFieldIterator<FProperty> It(StableAddScoreFunction); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			It->InitializeValue_InContainer(Params);
		}

		for (TFieldIterator<FProperty> It(StableAddScoreFunction); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			if (It->GetFName() == FName(TEXT("PointsToAdd")))
			{
				if (FIntProperty* IntProperty = CastField<FIntProperty>(*It))
				{
					IntProperty->SetPropertyValue_InContainer(Params, 1);
				}
			}
		}

		OrderManager->ProcessEvent(StableAddScoreFunction, Params);

		for (TFieldIterator<FProperty> It(StableAddScoreFunction); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			It->DestroyValue_InContainer(Params);
		}
	}
}

void UVRKitchenOrderValidationLibrary::SubmitCurrentPlateValidated(AActor* DeliveryArea, bool& OutOk)
{
	OutOk = false;
	if (!DeliveryArea)
	{
		return;
	}

	AActor* OrderManager = FindOrderManager(DeliveryArea->GetWorld());
	TArray<FName> RequiredTags;
	const bool bHasOrder = GetCurrentOrderRequiredTags(OrderManager, RequiredTags);
	const TArray<FSubmittedFood> SubmittedFoods = GatherSubmittedFoods(DeliveryArea);

	const bool bMatchesOrder = bHasOrder && SubmittedTagsMatchRequiredTags(SubmittedFoods, RequiredTags);
	if (bMatchesOrder)
	{
		CallStableAddScore(OrderManager);
		OutOk = true;
	}

	ClearSubmittedFoods(DeliveryArea, SubmittedFoods);
	SpawnFloatingFeedback(DeliveryArea, OutOk ? TEXT("ORDER OK") : TEXT("WRONG ORDER"), OutOk ? FColor::Green : FColor::Red);
}
