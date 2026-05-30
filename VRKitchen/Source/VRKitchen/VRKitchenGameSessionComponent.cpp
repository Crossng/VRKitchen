#include "VRKitchenGameSessionComponent.h"

#include "Components/SceneComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "UObject/UnrealType.h"

namespace
{
	struct FDemoOrderSpec
	{
		FString OrderName;
		TArray<FName> RequiredTags;
		FString DisplayDetails;
	};

	FDemoOrderSpec GetDemoOrderForProgress(const int32 CorrectOrders)
	{
		if (CorrectOrders < 2)
		{
			return {
				TEXT("经典汉堡"),
				{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Top_Bun")},
				TEXT("底部面包, 熟肉饼, 顶部面包"),
			};
		}

		if (CorrectOrders == 2)
		{
			return {
				TEXT("生菜汉堡"),
				{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Chopped_Lettuce"), TEXT("Top_Bun")},
				TEXT("底部面包, 熟肉饼, 切好的生菜, 顶部面包"),
			};
		}

		if (CorrectOrders == 3)
		{
			return {
				TEXT("番茄汉堡"),
				{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Chopped_Tomato"), TEXT("Top_Bun")},
				TEXT("底部面包, 熟肉饼, 切好的番茄, 顶部面包"),
			};
		}

		if (CorrectOrders == 4)
		{
			return {
				TEXT("厚肉生菜堡"),
				{TEXT("Bottom_Bun"), TEXT("Cooked_Meat"), TEXT("Chopped_Lettuce"), TEXT("Top_Bun")},
				TEXT("底部面包, 熟牛肉, 切好的生菜, 顶部面包"),
			};
		}

		return {
			TEXT("豪华双肉堡"),
			{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Chopped_Lettuce"), TEXT("Cooked_Meat"), TEXT("Chopped_Tomato"), TEXT("Top_Bun")},
			TEXT("底部面包, 熟肉饼, 切好的生菜, 熟牛肉, 切好的番茄, 顶部面包"),
		};
	}

	void SetOrderNameProperty(FProperty* Property, void* Container, const FString& Value)
	{
		if (FNameProperty* NameProperty = CastField<FNameProperty>(Property))
		{
			NameProperty->SetPropertyValue_InContainer(Container, FName(*Value));
		}
		else if (FStrProperty* StringProperty = CastField<FStrProperty>(Property))
		{
			StringProperty->SetPropertyValue_InContainer(Container, Value);
		}
		else if (FTextProperty* TextProperty = CastField<FTextProperty>(Property))
		{
			TextProperty->SetPropertyValue_InContainer(Container, FText::FromString(Value));
		}
	}

	void SetRequiredTagsProperty(FArrayProperty* ArrayProperty, void* Container, const TArray<FName>& RequiredTags)
	{
		if (!ArrayProperty)
		{
			return;
		}

		FScriptArrayHelper ArrayHelper(ArrayProperty, ArrayProperty->ContainerPtrToValuePtr<void>(Container));
		ArrayHelper.EmptyAndAddValues(RequiredTags.Num());
		for (int32 Index = 0; Index < RequiredTags.Num(); ++Index)
		{
			void* ElementPtr = ArrayHelper.GetRawPtr(Index);
			if (FNameProperty* NameProperty = CastField<FNameProperty>(ArrayProperty->Inner))
			{
				NameProperty->SetPropertyValue(ElementPtr, RequiredTags[Index]);
			}
			else if (FStrProperty* StringProperty = CastField<FStrProperty>(ArrayProperty->Inner))
			{
				StringProperty->SetPropertyValue(ElementPtr, RequiredTags[Index].ToString());
			}
		}
	}

	bool SetCurrentOrder(AActor* OrderManager, const FDemoOrderSpec& OrderSpec)
	{
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

		bool bSetRequiredTags = false;
		for (TFieldIterator<FProperty> It(CurrentOrderProperty->Struct); It; ++It)
		{
			FProperty* Property = *It;
			if (!Property)
			{
				continue;
			}

			if (Property->GetName().StartsWith(TEXT("OrderName")))
			{
				SetOrderNameProperty(Property, CurrentOrderPtr, OrderSpec.OrderName);
			}
			else if (Property->GetName().StartsWith(TEXT("RequiredTags")))
			{
				if (FArrayProperty* ArrayProperty = CastField<FArrayProperty>(Property))
				{
					SetRequiredTagsProperty(ArrayProperty, CurrentOrderPtr, OrderSpec.RequiredTags);
					bSetRequiredTags = true;
				}
			}
		}

		return bSetRequiredTags;
	}

	void SetManagerTextProperty(AActor* OrderManager, const FName PropertyName, const FString& Value)
	{
		if (!OrderManager)
		{
			return;
		}

		if (FStrProperty* StringProperty = FindFProperty<FStrProperty>(OrderManager->GetClass(), PropertyName))
		{
			StringProperty->SetPropertyValue_InContainer(OrderManager, Value);
		}
		else if (FTextProperty* TextProperty = FindFProperty<FTextProperty>(OrderManager->GetClass(), PropertyName))
		{
			TextProperty->SetPropertyValue_InContainer(OrderManager, FText::FromString(Value));
		}
	}

	void SetManagerIntProperty(AActor* OrderManager, const FName PropertyName, const int32 Value)
	{
		if (!OrderManager)
		{
			return;
		}

		if (FIntProperty* IntProperty = FindFProperty<FIntProperty>(OrderManager->GetClass(), PropertyName))
		{
			IntProperty->SetPropertyValue_InContainer(OrderManager, Value);
		}
	}

	int32 GetManagerScore(AActor* OrderManager)
	{
		if (!OrderManager)
		{
			return 0;
		}

		if (FIntProperty* IntProperty = FindFProperty<FIntProperty>(OrderManager->GetClass(), TEXT("GameScore")))
		{
			return IntProperty->GetPropertyValue_InContainer(OrderManager);
		}
		return 0;
	}

	void CallTabletRefresh(AActor* OrderManager, const FDemoOrderSpec& OrderSpec)
	{
		if (!OrderManager || !OrderManager->GetWorld())
		{
			return;
		}

		static const TCHAR* OrderTabletClassPath = TEXT("/Game/_Project/Gameplay/Orders/BP_OrderTablet.BP_OrderTablet_C");
		UClass* OrderTabletClass = StaticLoadClass(AActor::StaticClass(), nullptr, OrderTabletClassPath);
		AActor* OrderTablet = OrderTabletClass ? UGameplayStatics::GetActorOfClass(OrderManager->GetWorld(), OrderTabletClass) : nullptr;
		if (!OrderTablet)
		{
			return;
		}

		UFunction* RefreshFunction = OrderTablet->FindFunction(TEXT("RefreshTabletDisplay"));
		if (!RefreshFunction)
		{
			return;
		}

		uint8* Params = static_cast<uint8*>(FMemory_Alloca(RefreshFunction->ParmsSize));
		FMemory::Memzero(Params, RefreshFunction->ParmsSize);
		for (TFieldIterator<FProperty> It(RefreshFunction); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			It->InitializeValue_InContainer(Params);
		}

		for (TFieldIterator<FProperty> It(RefreshFunction); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			if (It->GetFName() == FName(TEXT("NewName")))
			{
				if (FStrProperty* StringProperty = CastField<FStrProperty>(*It))
				{
					StringProperty->SetPropertyValue_InContainer(Params, OrderSpec.OrderName);
				}
				else if (FTextProperty* TextProperty = CastField<FTextProperty>(*It))
				{
					TextProperty->SetPropertyValue_InContainer(Params, FText::FromString(OrderSpec.OrderName));
				}
				else if (FNameProperty* NameProperty = CastField<FNameProperty>(*It))
				{
					NameProperty->SetPropertyValue_InContainer(Params, FName(*OrderSpec.OrderName));
				}
			}
			else if (It->GetFName() == FName(TEXT("NewDetails")))
			{
				if (FStrProperty* StringProperty = CastField<FStrProperty>(*It))
				{
					StringProperty->SetPropertyValue_InContainer(Params, OrderSpec.DisplayDetails);
				}
				else if (FTextProperty* TextProperty = CastField<FTextProperty>(*It))
				{
					TextProperty->SetPropertyValue_InContainer(Params, FText::FromString(OrderSpec.DisplayDetails));
				}
			}
			else if (It->GetFName() == FName(TEXT("CurrentScore")))
			{
				if (FIntProperty* IntProperty = CastField<FIntProperty>(*It))
				{
					IntProperty->SetPropertyValue_InContainer(Params, GetManagerScore(OrderManager));
				}
				else if (FStrProperty* StringProperty = CastField<FStrProperty>(*It))
				{
					StringProperty->SetPropertyValue_InContainer(Params, FString::FromInt(GetManagerScore(OrderManager)));
				}
			}
		}

		OrderTablet->ProcessEvent(RefreshFunction, Params);

		for (TFieldIterator<FProperty> It(RefreshFunction); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			It->DestroyValue_InContainer(Params);
		}
	}
}

UVRKitchenGameSessionComponent::UVRKitchenGameSessionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
	PrimaryComponentTick.TickInterval = 0.1f;
}

void UVRKitchenGameSessionComponent::BeginPlay()
{
	Super::BeginPlay();
	EnsureTextComponents();
	if (bAutoStart)
	{
		StartSession();
	}
}

void UVRKitchenGameSessionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (bSessionActive)
	{
		RemainingSeconds = FMath::Max(0.0, RemainingSeconds - static_cast<double>(DeltaTime));
		if (RemainingSeconds <= 0.0)
		{
			EndSession();
		}
	}

	if (bSessionEnded)
	{
		if (UWorld* World = GetWorld())
		{
			if (APlayerController* PlayerController = World->GetFirstPlayerController())
			{
				if (PlayerController->WasInputKeyJustPressed(EKeys::R))
				{
					ResetSession();
				}
			}
		}
	}

	UpdateStatusText();
}

void UVRKitchenGameSessionComponent::StartSession()
{
	RemainingSeconds = SessionLengthSeconds;
	SessionScore = 0;
	CorrectOrders = 0;
	WrongOrders = 0;
	CurrentStreak = 0;
	BestStreak = 0;
	LastFeedbackMessage = TEXT("目标: 达到目标分并尽量保持连击");
	bSessionEnded = false;
	bMissionCleared = false;
	bSessionActive = true;

	SetManagerIntProperty(GetOwner(), TEXT("GameScore"), SessionScore);
	EnsureTextComponents();
	ApplyDemoOrderForProgress();
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(
			InitialOrderTimerHandle,
			this,
			&UVRKitchenGameSessionComponent::ApplyDemoOrderForProgress,
			0.5f,
			false);
	}
	UpdateStatusText();
}

void UVRKitchenGameSessionComponent::ResetSession()
{
	StartSession();
}

void UVRKitchenGameSessionComponent::EndSession()
{
	bSessionActive = false;
	bSessionEnded = true;
	RemainingSeconds = 0.0;
	UpdateStatusText();
}

void UVRKitchenGameSessionComponent::CompleteSession()
{
	bSessionActive = false;
	bSessionEnded = true;
	bMissionCleared = true;
	RemainingSeconds = 0.0;
	LastFeedbackMessage = TEXT("任务完成");
	UpdateStatusText();
}

bool UVRKitchenGameSessionComponent::CanAcceptOrders() const
{
	return bSessionActive && !bSessionEnded && RemainingSeconds > 0.0;
}

void UVRKitchenGameSessionComponent::RecordOrderSubmission(bool bWasCorrect, const FString& FeedbackMessage)
{
	if (!CanAcceptOrders())
	{
		return;
	}

	if (bWasCorrect)
	{
		++CorrectOrders;
		++CurrentStreak;
		BestStreak = FMath::Max(BestStreak, CurrentStreak);

		int32 ScoreDelta = CorrectOrderScore;
		const bool bEarnedStreakBonus = StreakBonusEvery > 0
			&& StreakBonusScore > 0
			&& CurrentStreak % StreakBonusEvery == 0;
		if (bEarnedStreakBonus)
		{
			ScoreDelta += StreakBonusScore;
		}

		SessionScore += ScoreDelta;
		LastFeedbackMessage = bEarnedStreakBonus
			? FString::Printf(TEXT("%s  连击奖励 +%d"), *FeedbackMessage, StreakBonusScore)
			: FeedbackMessage;
	}
	else
	{
		++WrongOrders;
		CurrentStreak = 0;
		SessionScore = FMath::Max(0, SessionScore - WrongOrderPenalty);
		LastFeedbackMessage = FeedbackMessage;
	}

	SetManagerIntProperty(GetOwner(), TEXT("GameScore"), SessionScore);
	if (bWasCorrect && TargetScore > 0 && !bMissionCleared && SessionScore >= TargetScore)
	{
		CompleteSession();
	}
	UpdateStatusText();
}

void UVRKitchenGameSessionComponent::ApplyDemoOrderForProgress()
{
	if (!CanAcceptOrders())
	{
		return;
	}

	AActor* OrderManager = GetOwner();
	if (!OrderManager)
	{
		return;
	}

	const FDemoOrderSpec OrderSpec = GetDemoOrderForProgress(CorrectOrders);
	if (SetCurrentOrder(OrderManager, OrderSpec))
	{
		SetManagerTextProperty(OrderManager, TEXT("TempIngredientsText"), OrderSpec.DisplayDetails);
		CallTabletRefresh(OrderManager, OrderSpec);
	}
}

int32 UVRKitchenGameSessionComponent::GetStarRating() const
{
	if (SessionScore >= ThreeStarScore)
	{
		return 3;
	}

	if (SessionScore >= TwoStarScore)
	{
		return 2;
	}

	if (SessionScore >= OneStarScore)
	{
		return 1;
	}

	return 0;
}

FString UVRKitchenGameSessionComponent::GetResultTitle() const
{
	return SessionScore >= TargetScore ? TEXT("挑战成功") : TEXT("继续练习");
}

FString UVRKitchenGameSessionComponent::GetResultGradeText() const
{
	switch (GetStarRating())
	{
	case 3:
		return TEXT("三星");
	case 2:
		return TEXT("二星");
	case 1:
		return TEXT("一星");
	default:
		return TEXT("未达标");
	}
}

void UVRKitchenGameSessionComponent::EnsureTextComponents()
{
	AActor* Owner = GetOwner();
	if (!Owner)
	{
		return;
	}

	USceneComponent* RootComponent = Owner->GetRootComponent();
	if (!StatusTextComponent)
	{
		StatusTextComponent = NewObject<UTextRenderComponent>(Owner, TEXT("VRKitchenSessionStatusText"));
		StatusTextComponent->SetHorizontalAlignment(EHTA_Left);
		StatusTextComponent->SetVerticalAlignment(EVRTA_TextCenter);
		StatusTextComponent->SetWorldSize(18.0f);
		StatusTextComponent->SetTextRenderColor(FColor::Cyan);
		StatusTextComponent->SetRelativeLocation(FVector(0.0f, -120.0f, 120.0f));
		if (RootComponent)
		{
			StatusTextComponent->SetupAttachment(RootComponent);
		}
		StatusTextComponent->RegisterComponent();
	}

	if (!TutorialTextComponent)
	{
		TutorialTextComponent = NewObject<UTextRenderComponent>(Owner, TEXT("VRKitchenTutorialText"));
		TutorialTextComponent->SetHorizontalAlignment(EHTA_Left);
		TutorialTextComponent->SetVerticalAlignment(EVRTA_TextCenter);
		TutorialTextComponent->SetWorldSize(14.0f);
		TutorialTextComponent->SetTextRenderColor(FColor::White);
		TutorialTextComponent->SetRelativeLocation(FVector(0.0f, -120.0f, 210.0f));
		TutorialTextComponent->SetText(FText::FromString(BuildTutorialText()));
		if (RootComponent)
		{
			TutorialTextComponent->SetupAttachment(RootComponent);
		}
		TutorialTextComponent->RegisterComponent();
	}
}

void UVRKitchenGameSessionComponent::UpdateStatusText()
{
	EnsureTextComponents();
	if (StatusTextComponent)
	{
		StatusTextComponent->SetText(FText::FromString(BuildStatusText()));
	}
}

FString UVRKitchenGameSessionComponent::BuildStatusText() const
{
	const int32 RemainingWholeSeconds = FMath::Max(0, FMath::CeilToInt(RemainingSeconds));
	const int32 Minutes = RemainingWholeSeconds / 60;
	const int32 Seconds = RemainingWholeSeconds % 60;

	if (bSessionEnded)
	{
		const FString ResultStatus = bMissionCleared ? TEXT("任务完成") : TEXT("时间到");
		return FString::Printf(
			TEXT("%s - %s\n总分: %d / 目标: %d\n评级: %s\n完成: %d  错误: %d\n最佳连击: %d\n按 R 重新开始"),
			*ResultStatus,
			*GetResultTitle(),
			SessionScore,
			TargetScore,
			*GetResultGradeText(),
			CorrectOrders,
			WrongOrders,
			BestStreak);
	}

	return FString::Printf(
		TEXT("剩余时间: %02d:%02d\n分数: %d / 目标: %d\n完成: %d  错误: %d  连击: %d\n%s"),
		Minutes,
		Seconds,
		SessionScore,
		TargetScore,
		CorrectOrders,
		WrongOrders,
		CurrentStreak,
		*LastFeedbackMessage);
}

FString UVRKitchenGameSessionComponent::BuildTutorialText() const
{
	return TEXT("玩法提示\n1. 查看订单\n2. 处理食材\n3. 煎熟肉饼\n4. 按顺序叠到盘子\n5. 放到出餐区提交\n连续正确 3 单有奖励");
}
