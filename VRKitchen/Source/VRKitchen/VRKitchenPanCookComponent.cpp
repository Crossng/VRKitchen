#include "VRKitchenPanCookComponent.h"

#include "Components/PrimitiveComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/TextRenderComponent.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "TimerManager.h"
#include "UObject/UnrealType.h"

namespace
{
	const FName TagRawMeat(TEXT("Raw_Meat"));
	const FName TagCookedMeat(TEXT("Cooked_Meat"));
	const FName TagBurntMeat(TEXT("Burnt_Meat"));
	const FName TagRawPatty(TEXT("Raw_Patty"));
	const FName TagCookedPatty(TEXT("Cooked_Patty"));
	const FName TagBurntPatty(TEXT("Burnt_Patty"));
	const FName TagOnStove(TEXT("OnStove"));

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

	bool GetBoolProperty(UObject* Object, const FName PropertyName)
	{
		if (!Object)
		{
			return false;
		}

		if (FBoolProperty* BoolProperty = FindFProperty<FBoolProperty>(Object->GetClass(), PropertyName))
		{
			return BoolProperty->GetPropertyValue_InContainer(Object);
		}
		return false;
	}

	double GetNumericProperty(UObject* Object, const FName PropertyName)
	{
		if (!Object)
		{
			return 0.0;
		}

		if (FDoubleProperty* DoubleProperty = FindFProperty<FDoubleProperty>(Object->GetClass(), PropertyName))
		{
			return DoubleProperty->GetPropertyValue_InContainer(Object);
		}
		if (FFloatProperty* FloatProperty = FindFProperty<FFloatProperty>(Object->GetClass(), PropertyName))
		{
			return FloatProperty->GetPropertyValue_InContainer(Object);
		}
		return 0.0;
	}

	void SetNumericProperty(UObject* Object, const FName PropertyName, const double Value)
	{
		if (!Object)
		{
			return;
		}

		if (FDoubleProperty* DoubleProperty = FindFProperty<FDoubleProperty>(Object->GetClass(), PropertyName))
		{
			DoubleProperty->SetPropertyValue_InContainer(Object, Value);
		}
		else if (FFloatProperty* FloatProperty = FindFProperty<FFloatProperty>(Object->GetClass(), PropertyName))
		{
			FloatProperty->SetPropertyValue_InContainer(Object, static_cast<float>(Value));
		}
	}

	UStaticMesh* GetCookedMesh(AActor* FoodActor)
	{
		if (!FoodActor)
		{
			return nullptr;
		}

		if (FObjectPropertyBase* CookedMeshProperty = FindFProperty<FObjectPropertyBase>(FoodActor->GetClass(), TEXT("CookedMesh")))
		{
			return Cast<UStaticMesh>(CookedMeshProperty->GetObjectPropertyValue_InContainer(FoodActor));
		}
		return nullptr;
	}

	void SetFoodStaticMesh(AActor* FoodActor, UStaticMesh* CookedMesh)
	{
		if (!FoodActor || !CookedMesh)
		{
			return;
		}

		if (UStaticMeshComponent* StaticMeshComponent = FindComponentByName<UStaticMeshComponent>(FoodActor, TEXT("StaticMesh")))
		{
			StaticMeshComponent->SetStaticMesh(CookedMesh);
		}
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
		TextComponent->SetWorldSize(18.0f);
		TextComponent->SetRelativeLocation(FVector(0.0f, 0.0f, 28.0f));
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

	bool CookFoodActor(AActor* FoodActor, const FName RawTag, const FName CookedTag, const double DeltaTime, const double CookTimeSeconds)
	{
		if (!FoodActor || !FoodActor->Tags.Contains(RawTag) || FoodActor->Tags.Contains(CookedTag))
		{
			return false;
		}

		const double NewCookTime = GetNumericProperty(FoodActor, TEXT("Cooktime")) + DeltaTime;
		SetNumericProperty(FoodActor, TEXT("Cooktime"), NewCookTime);

		if (NewCookTime < CookTimeSeconds)
		{
			return true;
		}

		FoodActor->Tags.Remove(RawTag);
		FoodActor->Tags.AddUnique(CookedTag);
		SetFoodStaticMesh(FoodActor, GetCookedMesh(FoodActor));
		SetNumericProperty(FoodActor, TEXT("Cooktime"), CookTimeSeconds);
		SpawnFloatingFeedback(FoodActor, TEXT("已煎熟"), FColor::Orange);
		return true;
	}

	bool OvercookFoodActor(AActor* FoodActor, const FName CookedTag, const FName BurntTag, const double DeltaTime, const double OvercookTimeSeconds, TMap<TWeakObjectPtr<AActor>, double>& OvercookTimes)
	{
		if (!FoodActor || !FoodActor->Tags.Contains(CookedTag) || FoodActor->Tags.Contains(BurntTag))
		{
			return false;
		}

		double& HeatTime = OvercookTimes.FindOrAdd(FoodActor);
		HeatTime += DeltaTime;
		if (HeatTime < OvercookTimeSeconds)
		{
			return true;
		}

		FoodActor->Tags.Remove(CookedTag);
		FoodActor->Tags.AddUnique(BurntTag);
		SpawnFloatingFeedback(FoodActor, TEXT("烧焦了"), FColor::Red);
		return true;
	}
}

UVRKitchenPanCookComponent::UVRKitchenPanCookComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
}

void UVRKitchenPanCookComponent::BeginPlay()
{
	Super::BeginPlay();
	SetComponentTickEnabled(true);
}

void UVRKitchenPanCookComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	AActor* Owner = GetOwner();
	if (!Owner || (!GetBoolProperty(Owner, TEXT("IsOnStove")) && !Owner->Tags.Contains(TagOnStove)))
	{
		return;
	}

	UPrimitiveComponent* CookZone = FindComponentByName<UPrimitiveComponent>(Owner, TEXT("Box"));
	if (!CookZone)
	{
		return;
	}

	TArray<AActor*> CandidateActors;
	TSet<AActor*> SeenActors;

	auto AddCandidate = [&CandidateActors, &SeenActors, Owner](AActor* Candidate)
	{
		if (Candidate && Candidate != Owner && !SeenActors.Contains(Candidate))
		{
			SeenActors.Add(Candidate);
			CandidateActors.Add(Candidate);
		}
	};

	TArray<AActor*> OverlappingActors;
	CookZone->GetOverlappingActors(OverlappingActors);
	for (AActor* OverlappingActor : OverlappingActors)
	{
		AddCandidate(OverlappingActor);
	}

	TArray<AActor*> AttachedActors;
	Owner->GetAttachedActors(AttachedActors, true, true);
	for (AActor* AttachedActor : AttachedActors)
	{
		AddCandidate(AttachedActor);
	}

	if (UWorld* World = Owner->GetWorld())
	{
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			AActor* Candidate = *It;
			if (!Candidate || Candidate == Owner)
			{
				continue;
			}

			if (Candidate->GetAttachParentActor() == Owner)
			{
				AddCandidate(Candidate);
				continue;
			}

			if (USceneComponent* CandidateRoot = Candidate->GetRootComponent())
			{
				if (USceneComponent* AttachParent = CandidateRoot->GetAttachParent())
				{
					if (AttachParent->GetOwner() == Owner)
					{
						AddCandidate(Candidate);
					}
				}
			}
		}
	}

	for (AActor* FoodActor : CandidateActors)
	{
		if (!FoodActor || FoodActor == Owner)
		{
			continue;
		}

		if (CookFoodActor(FoodActor, TagRawMeat, TagCookedMeat, DeltaTime, CookTimeSeconds))
		{
			continue;
		}

		if (CookFoodActor(FoodActor, TagRawPatty, TagCookedPatty, DeltaTime, CookTimeSeconds))
		{
			continue;
		}

		if (OvercookFoodActor(FoodActor, TagCookedMeat, TagBurntMeat, DeltaTime, OvercookTimeSeconds, OvercookTimes))
		{
			continue;
		}

		OvercookFoodActor(FoodActor, TagCookedPatty, TagBurntPatty, DeltaTime, OvercookTimeSeconds, OvercookTimes);
	}
}
