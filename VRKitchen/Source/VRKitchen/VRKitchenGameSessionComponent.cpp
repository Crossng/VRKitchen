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

	struct FDemoMenuStep
	{
		int32 FirstCorrectOrderCount = 0;
		FString StageText;
		FString NextGoalText;
		FString TutorialText;
		FString ActionStepText;
		FDemoOrderSpec OrderSpec;
	};

	const TArray<FDemoMenuStep>& GetDemoMenuRoute()
	{
		static const TArray<FDemoMenuStep> Route = {
			{
				0,
				TEXT("基础汉堡训练"),
				TEXT("先稳定完成 2 单经典汉堡"),
				TEXT("经典汉堡：底部面包 + 熟肉饼 + 顶部面包。"),
				TEXT("先取底部面包，再煎熟肉饼，最后盖上顶部面包后出餐。"),
				{
					TEXT("经典汉堡"),
					{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Top_Bun")},
					TEXT("底部面包, 熟肉饼, 顶部面包"),
				},
			},
			{
				2,
				TEXT("牛排煎制"),
				TEXT("用煎锅和灶台做香煎牛排"),
				TEXT("香煎牛排：把生牛肉放进煎锅，锅在灶台上加热到熟牛肉后再出餐。"),
				TEXT("把生牛肉放进煎锅，确认锅在灶台上，变成熟牛肉后立刻装盘。"),
				{
					TEXT("香煎牛排"),
					{TEXT("Cooked_Meat")},
					TEXT("熟牛肉"),
				},
			},
			{
				3,
				TEXT("沙拉切配"),
				TEXT("切生菜和番茄做田园沙拉"),
				TEXT("田园沙拉：切好生菜和番茄后直接叠盘出餐，不需要煎锅。"),
				TEXT("先切生菜，再切番茄，按生菜到番茄的顺序放盘。"),
				{
					TEXT("田园沙拉"),
					{TEXT("Chopped_Lettuce"), TEXT("Chopped_Tomato")},
					TEXT("切好的生菜, 切好的番茄"),
				},
			},
			{
				4,
				TEXT("生菜汉堡进阶"),
				TEXT("把切好的生菜加入汉堡"),
				TEXT("生菜汉堡：先切生菜，再放到熟肉饼上方。"),
				TEXT("先做底部面包和熟肉饼，再加入切好的生菜，最后盖顶部面包。"),
				{
					TEXT("生菜汉堡"),
					{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Chopped_Lettuce"), TEXT("Top_Bun")},
					TEXT("底部面包, 熟肉饼, 切好的生菜, 顶部面包"),
				},
			},
			{
				5,
				TEXT("番茄切配"),
				TEXT("切番茄，注意不要换顺序"),
				TEXT("番茄汉堡：先切番茄，叠盘顺序仍然严格。"),
				TEXT("先做底部面包和熟肉饼，再加入切好的番茄，最后盖顶部面包。"),
				{
					TEXT("番茄汉堡"),
					{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Chopped_Tomato"), TEXT("Top_Bun")},
					TEXT("底部面包, 熟肉饼, 切好的番茄, 顶部面包"),
				},
			},
			{
				6,
				TEXT("厚肉煎制"),
				TEXT("煎熟牛肉再提交厚肉堡"),
				TEXT("厚肉生菜堡：使用熟牛肉，不要提交生肉或烧焦肉。"),
				TEXT("把牛肉煎熟，和切好的生菜夹进面包；不要让牛肉继续受热烧焦。"),
				{
					TEXT("厚肉生菜堡"),
					{TEXT("Bottom_Bun"), TEXT("Cooked_Meat"), TEXT("Chopped_Lettuce"), TEXT("Top_Bun")},
					TEXT("底部面包, 熟牛肉, 切好的生菜, 顶部面包"),
				},
			},
			{
				7,
				TEXT("豪华双肉挑战"),
				TEXT("完成豪华双肉堡，准备套餐挑战"),
				TEXT("豪华双肉堡：肉饼、生菜、熟牛肉、番茄都要按订单顺序。"),
				TEXT("按顺序放底部面包、熟肉饼、生菜、熟牛肉、番茄、顶部面包。"),
				{
					TEXT("豪华双肉堡"),
					{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Chopped_Lettuce"), TEXT("Cooked_Meat"), TEXT("Chopped_Tomato"), TEXT("Top_Bun")},
					TEXT("底部面包, 熟肉饼, 切好的生菜, 熟牛肉, 切好的番茄, 顶部面包"),
				},
			},
			{
				8,
				TEXT("牛排沙拉套餐"),
				TEXT("把牛排和沙拉按套餐顺序出餐"),
				TEXT("牛排沙拉套餐：先放熟牛肉，再放切好的生菜和番茄。"),
				TEXT("先煎熟牛肉放盘，再补切好的生菜和切好的番茄。"),
				{
					TEXT("牛排沙拉套餐"),
					{TEXT("Cooked_Meat"), TEXT("Chopped_Lettuce"), TEXT("Chopped_Tomato")},
					TEXT("熟牛肉, 切好的生菜, 切好的番茄"),
				},
			},
			{
				9,
				TEXT("汉堡沙拉套餐"),
				TEXT("完成经典汉堡沙拉套餐冲三星"),
				TEXT("经典汉堡沙拉套餐：先完成经典汉堡，再补上沙拉配菜。"),
				TEXT("先叠完整经典汉堡，再按生菜、番茄顺序补上沙拉配菜。"),
				{
					TEXT("经典汉堡沙拉套餐"),
					{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Top_Bun"), TEXT("Chopped_Lettuce"), TEXT("Chopped_Tomato")},
					TEXT("底部面包, 熟肉饼, 顶部面包, 切好的生菜, 切好的番茄"),
				},
			},
		};
		return Route;
	}

	int32 GetMenuStepIndexForProgress(const int32 CorrectOrders)
	{
		const TArray<FDemoMenuStep>& Route = GetDemoMenuRoute();
		for (int32 Index = Route.Num() - 1; Index >= 0; --Index)
		{
			if (CorrectOrders >= Route[Index].FirstCorrectOrderCount)
			{
				return Index;
			}
		}
		return 0;
	}

	const FDemoMenuStep& GetDemoMenuStepForProgress(const int32 CorrectOrders)
	{
		const TArray<FDemoMenuStep>& Route = GetDemoMenuRoute();
		return Route[FMath::Clamp(GetMenuStepIndexForProgress(CorrectOrders), 0, Route.Num() - 1)];
	}

	FDemoOrderSpec GetDemoOrderForProgress(const int32 CorrectOrders)
	{
		return GetDemoMenuStepForProgress(CorrectOrders).OrderSpec;
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
	LastFeedbackMessage = TEXT("目标: 达到目标分，连续正确 3 单有奖励");
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

int32 UVRKitchenGameSessionComponent::GetTotalOrderAttempts() const
{
	return CorrectOrders + WrongOrders;
}

int32 UVRKitchenGameSessionComponent::GetAccuracyPercent() const
{
	const int32 TotalAttempts = GetTotalOrderAttempts();
	if (TotalAttempts <= 0)
	{
		return 0;
	}
	return FMath::RoundToInt(static_cast<float>(CorrectOrders) * 100.0f / static_cast<float>(TotalAttempts));
}

FString UVRKitchenGameSessionComponent::GetAccuracyText() const
{
	const int32 TotalAttempts = GetTotalOrderAttempts();
	if (TotalAttempts <= 0)
	{
		return TEXT("准确率: 暂无提交");
	}

	return FString::Printf(
		TEXT("准确率: %d%% (%d/%d)"),
		GetAccuracyPercent(),
		CorrectOrders,
		TotalAttempts);
}

FString UVRKitchenGameSessionComponent::GetMistakeSummaryText() const
{
	if (WrongOrders <= 0)
	{
		return TEXT("错误复盘: 没有错误订单，节奏很稳。");
	}

	if (WrongOrders == 1)
	{
		return TEXT("错误复盘: 只有 1 次错误，下一局重点保持当前顺序和处理节奏。");
	}

	return FString::Printf(
		TEXT("错误复盘: 共 %d 次错误，优先放慢提交前检查，确认食材状态和叠放顺序。"),
		WrongOrders);
}

FString UVRKitchenGameSessionComponent::GetNextRunFocusText() const
{
	if (CorrectOrders <= 0)
	{
		return TEXT("下一局重点: 先完成第一单经典汉堡，熟悉拿取、煎肉和出餐。");
	}

	if (WrongOrders > CorrectOrders)
	{
		return TEXT("下一局重点: 先保证正确率，提交前逐项对照订单，不急着冲速度。");
	}

	if (BestStreak < StreakBonusEvery)
	{
		return TEXT("下一局重点: 争取连续正确 3 单，触发连击奖励。");
	}

	if (GetCurrentMenuRouteStep() < GetMenuRouteTotal())
	{
		return FString::Printf(
			TEXT("下一局重点: 推进到第 %d/%d 阶段，练会 %s。"),
			GetCurrentMenuRouteStep(),
			GetMenuRouteTotal(),
			*GetCurrentMenuItemText());
	}

	if (!bMissionCleared)
	{
		return TEXT("下一局重点: 菜单路线已经跑完，减少错误扣分冲三星目标。");
	}

	return TEXT("下一局重点: 已完成三星路线，可以挑战更少错误和更高连击。");
}

FString UVRKitchenGameSessionComponent::GetPerformanceSummaryText() const
{
	return FString::Printf(
		TEXT("本局复盘\n%s\n%s\n最佳连击: %d\n%s"),
		*GetAccuracyText(),
		*GetMistakeSummaryText(),
		BestStreak,
		*GetNextRunFocusText());
}

int32 UVRKitchenGameSessionComponent::GetMenuRouteTotal() const
{
	return GetDemoMenuRoute().Num();
}

int32 UVRKitchenGameSessionComponent::GetCurrentMenuRouteStep() const
{
	return GetMenuStepIndexForProgress(CorrectOrders) + 1;
}

FString UVRKitchenGameSessionComponent::GetCurrentMenuItemText() const
{
	const FDemoMenuStep& Step = GetDemoMenuStepForProgress(CorrectOrders);
	return FString::Printf(TEXT("%s：%s"), *Step.OrderSpec.OrderName, *Step.OrderSpec.DisplayDetails);
}

FString UVRKitchenGameSessionComponent::GetMenuRouteText() const
{
	TArray<FString> MenuItems;
	const TArray<FDemoMenuStep>& Route = GetDemoMenuRoute();
	for (int32 Index = 0; Index < Route.Num(); ++Index)
	{
		MenuItems.Add(FString::Printf(TEXT("%d.%s"), Index + 1, *Route[Index].OrderSpec.OrderName));
	}
	return FString::Printf(TEXT("菜单路线：%s"), *FString::Join(MenuItems, TEXT(" -> ")));
}

FString UVRKitchenGameSessionComponent::GetMenuProgressText() const
{
	return FString::Printf(
		TEXT("菜单进度: %d/%d  当前: %s"),
		GetCurrentMenuRouteStep(),
		GetMenuRouteTotal(),
		*GetCurrentMenuItemText());
}

FString UVRKitchenGameSessionComponent::GetCurrentStageUnlockText() const
{
	const FDemoMenuStep& Step = GetDemoMenuStepForProgress(CorrectOrders);
	if (Step.FirstCorrectOrderCount <= 0)
	{
		return TEXT("阶段解锁: 开局基础训练，先熟悉拿取、煎肉、叠盘和出餐。");
	}

	return FString::Printf(
		TEXT("阶段解锁: 已完成 %d 单正确订单，解锁「%s」。"),
		Step.FirstCorrectOrderCount,
		*Step.StageText);
}

int32 UVRKitchenGameSessionComponent::GetCorrectOrdersUntilNextStage() const
{
	const TArray<FDemoMenuStep>& Route = GetDemoMenuRoute();
	const int32 CurrentStepIndex = GetMenuStepIndexForProgress(CorrectOrders);
	for (int32 Index = CurrentStepIndex + 1; Index < Route.Num(); ++Index)
	{
		if (Route[Index].FirstCorrectOrderCount > CorrectOrders)
		{
			return Route[Index].FirstCorrectOrderCount - CorrectOrders;
		}
	}
	return 0;
}

FString UVRKitchenGameSessionComponent::GetNextStagePreviewText() const
{
	const TArray<FDemoMenuStep>& Route = GetDemoMenuRoute();
	const int32 CurrentStepIndex = GetMenuStepIndexForProgress(CorrectOrders);
	for (int32 Index = CurrentStepIndex + 1; Index < Route.Num(); ++Index)
	{
		if (Route[Index].FirstCorrectOrderCount > CorrectOrders)
		{
			return FString::Printf(
				TEXT("下一阶段: 再正确完成 %d 单，解锁 %d/%d「%s」-%s。"),
				Route[Index].FirstCorrectOrderCount - CorrectOrders,
				Index + 1,
				Route.Num(),
				*Route[Index].OrderSpec.OrderName,
				*Route[Index].StageText);
		}
	}

	return TEXT("下一阶段: 已到最终菜单，目标是减少错误并冲三星。");
}

FString UVRKitchenGameSessionComponent::GetLearningPathText() const
{
	TArray<FString> Items;
	const TArray<FDemoMenuStep>& Route = GetDemoMenuRoute();
	const int32 CurrentStepIndex = GetMenuStepIndexForProgress(CorrectOrders);
	for (int32 Index = 0; Index < Route.Num(); ++Index)
	{
		FString StateText = TEXT("待解锁");
		if (Index < CurrentStepIndex)
		{
			StateText = TEXT("已完成");
		}
		else if (Index == CurrentStepIndex)
		{
			StateText = TEXT("当前");
		}

		Items.Add(FString::Printf(TEXT("%d.%s[%s]"), Index + 1, *Route[Index].OrderSpec.OrderName, *StateText));
	}

	return FString::Printf(TEXT("学习路线: %s"), *FString::Join(Items, TEXT(" -> ")));
}

FString UVRKitchenGameSessionComponent::GetStageCoachingText() const
{
	return FString::Printf(
		TEXT("%s\n%s\n%s"),
		*GetCurrentStageUnlockText(),
		*GetNextStagePreviewText(),
		*GetLearningPathText());
}

FString UVRKitchenGameSessionComponent::GetCurrentRequiredIngredientsText() const
{
	const FDemoOrderSpec& OrderSpec = GetDemoMenuStepForProgress(CorrectOrders).OrderSpec;
	return FString::Printf(TEXT("所需食材: %s"), *OrderSpec.DisplayDetails);
}

FString UVRKitchenGameSessionComponent::GetCurrentActionStepText() const
{
	return FString::Printf(TEXT("推荐步骤: %s"), *GetDemoMenuStepForProgress(CorrectOrders).ActionStepText);
}

FString UVRKitchenGameSessionComponent::GetFailureRecoveryText() const
{
	if (LastFeedbackMessage.IsEmpty() || LastFeedbackMessage.Contains(TEXT("出餐成功")) || LastFeedbackMessage.Contains(TEXT("目标:")) || LastFeedbackMessage.Contains(TEXT("任务完成")))
	{
		return TEXT("修复建议: 保持当前节奏，按订单顺序继续出餐。");
	}

	if (LastFeedbackMessage.Contains(TEXT("请先放上食材")))
	{
		return TEXT("修复建议: 先查看所需食材，把第一项食材放到盘子或出餐区。");
	}

	if (LastFeedbackMessage.Contains(TEXT("还没切")))
	{
		return TEXT("修复建议: 把对应蔬菜放到切菜板处理，生成切好的生菜或番茄后再提交。");
	}

	if (LastFeedbackMessage.Contains(TEXT("还没煎熟")))
	{
		return TEXT("修复建议: 把生肉放进煎锅，并确认煎锅在灶台上加热到熟。");
	}

	if (LastFeedbackMessage.Contains(TEXT("烧焦")))
	{
		return TEXT("修复建议: 丢弃烧焦食材，重新煎一份；熟了就尽快离开灶台。");
	}

	if (LastFeedbackMessage.Contains(TEXT("缺少")))
	{
		return TEXT("修复建议: 对照所需食材补齐缺失项，再按当前订单顺序提交。");
	}

	if (LastFeedbackMessage.Contains(TEXT("多了")))
	{
		return TEXT("修复建议: 清理盘子上的多余食材，只保留订单需要的内容。");
	}

	if (LastFeedbackMessage.Contains(TEXT("顺序错误")))
	{
		return TEXT("修复建议: 清空后按订单从左到右、从下到上重新叠放。");
	}

	if (LastFeedbackMessage.Contains(TEXT("未知食材")))
	{
		return TEXT("修复建议: 移除未识别物体，只使用当前菜单里的正式食材。");
	}

	return TEXT("修复建议: 查看失败原因，按所需食材和推荐步骤重新制作。");
}

FString UVRKitchenGameSessionComponent::GetPlayerObjectiveText() const
{
	return FString::Printf(
		TEXT("%s\n%s\n%s\n%s\n%s"),
		*GetMenuProgressText(),
		*GetStageCoachingText(),
		*GetCurrentRequiredIngredientsText(),
		*GetCurrentActionStepText(),
		*GetFailureRecoveryText());
}

int32 UVRKitchenGameSessionComponent::GetOrderStageIndex() const
{
	return GetCurrentMenuRouteStep();
}

FString UVRKitchenGameSessionComponent::GetOrderStageText() const
{
	return GetDemoMenuStepForProgress(CorrectOrders).StageText;
}

int32 UVRKitchenGameSessionComponent::GetUrgencyLevel() const
{
	if (!bSessionActive || bSessionEnded)
	{
		return 0;
	}

	if (CriticalTimeSeconds > 0.0 && RemainingSeconds <= CriticalTimeSeconds)
	{
		return 2;
	}

	if (WarningTimeSeconds > 0.0 && RemainingSeconds <= WarningTimeSeconds)
	{
		return 1;
	}

	return 0;
}

FString UVRKitchenGameSessionComponent::GetUrgencyText() const
{
	switch (GetUrgencyLevel())
	{
	case 2:
		return TEXT("最后冲刺");
	case 1:
		return TEXT("注意时间");
	default:
		return bSessionEnded ? TEXT("已结算") : TEXT("节奏稳定");
	}
}

FString UVRKitchenGameSessionComponent::GetNextGoalText() const
{
	if (bSessionEnded)
	{
		return bMissionCleared ? TEXT("按 R 再挑战三星节奏") : TEXT("按 R 重新练习流程");
	}

	const int32 MissingScore = TargetScore > 0 ? FMath::Max(0, TargetScore - SessionScore) : 0;
	const FString ScoreGoal = TargetScore > 0
		? FString::Printf(TEXT("还差 %d 分达成目标"), MissingScore)
		: TEXT("自由练习");

	return FString::Printf(TEXT("%s；%s"), *ScoreGoal, *GetDemoMenuStepForProgress(CorrectOrders).NextGoalText);
}

FString UVRKitchenGameSessionComponent::GetTutorialHintText() const
{
	if (bSessionEnded)
	{
		return bMissionCleared
			? FString::Printf(TEXT("挑战完成：%s 按 R 可以再跑一局。"), *GetNextRunFocusText())
			: FString::Printf(TEXT("时间到：%s 按 R 重开。"), *GetNextRunFocusText());
	}

	FString Prefix;
	if (GetUrgencyLevel() == 2)
	{
		Prefix = TEXT("时间紧张：优先完成当前订单。\n");
	}
	else if (GetUrgencyLevel() == 1)
	{
		Prefix = TEXT("注意时间：动作保持连贯。\n");
	}
	else if (WrongOrders > 0 && CurrentStreak == 0)
	{
		Prefix = FString::Printf(TEXT("刚才出错：%s\n"), *GetFailureRecoveryText());
	}

	return Prefix + GetDemoMenuStepForProgress(CorrectOrders).TutorialText + TEXT("\n") + GetNextStagePreviewText() + TEXT("\n") + GetCurrentActionStepText();
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
		StatusTextComponent->SetTextRenderColor(GetStatusTextColor());
	}
	if (TutorialTextComponent)
	{
		TutorialTextComponent->SetText(FText::FromString(BuildTutorialText()));
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
			TEXT("%s - %s\n总分: %d / 目标: %d\n评级: %s\n完成: %d  错误: %d\n%s\n按 R 重新开始"),
			*ResultStatus,
			*GetResultTitle(),
			SessionScore,
			TargetScore,
			*GetResultGradeText(),
			CorrectOrders,
			WrongOrders,
			*GetPerformanceSummaryText());
	}

	return FString::Printf(
		TEXT("剩余时间: %02d:%02d  %s\n阶段: %s\n%s\n分数: %d / 目标: %d\n完成: %d  错误: %d  连击: %d\n下一目标: %s\n%s\n%s"),
		Minutes,
		Seconds,
		*GetUrgencyText(),
		*GetOrderStageText(),
		*GetPlayerObjectiveText(),
		SessionScore,
		TargetScore,
		CorrectOrders,
		WrongOrders,
		CurrentStreak,
		*GetNextGoalText(),
		*LastFeedbackMessage,
		*GetFailureRecoveryText());
}

FString UVRKitchenGameSessionComponent::BuildTutorialText() const
{
	return FString::Printf(
		TEXT("玩法提示\n%s\n%s\n步骤: 看订单 -> 切菜/煎肉 -> 按顺序叠盘 -> 出餐\n连续正确 3 单有奖励"),
		*GetCurrentRequiredIngredientsText(),
		*GetTutorialHintText());
}

FColor UVRKitchenGameSessionComponent::GetStatusTextColor() const
{
	if (bSessionEnded)
	{
		return bMissionCleared ? FColor::Green : FColor::Yellow;
	}

	switch (GetUrgencyLevel())
	{
	case 2:
		return FColor::Red;
	case 1:
		return FColor::Orange;
	default:
		return FColor::Cyan;
	}
}
