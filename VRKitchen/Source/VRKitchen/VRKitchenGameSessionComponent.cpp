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
				TEXT("田园沙拉"),
				{TEXT("Chopped_Lettuce"), TEXT("Chopped_Tomato")},
				TEXT("切好的生菜, 切好的番茄"),
			};
		}

		if (CorrectOrders == 3)
		{
			return {
				TEXT("生菜汉堡"),
				{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Chopped_Lettuce"), TEXT("Top_Bun")},
				TEXT("底部面包, 熟肉饼, 切好的生菜, 顶部面包"),
			};
		}

		if (CorrectOrders == 4)
		{
			return {
				TEXT("番茄汉堡"),
				{TEXT("Bottom_Bun"), TEXT("Cooked_Patty"), TEXT("Chopped_Tomato"), TEXT("Top_Bun")},
				TEXT("底部面包, 熟肉饼, 切好的番茄, 顶部面包"),
			};
		}

		if (CorrectOrders == 5)
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

int32 UVRKitchenGameSessionComponent::GetOrderStageIndex() const
{
	if (CorrectOrders < 2)
	{
		return 1;
	}

	if (CorrectOrders == 2)
	{
		return 2;
	}

	if (CorrectOrders == 3)
	{
		return 3;
	}

	if (CorrectOrders == 4)
	{
		return 4;
	}

	if (CorrectOrders == 5)
	{
		return 5;
	}

	return 6;
}

FString UVRKitchenGameSessionComponent::GetOrderStageText() const
{
	switch (GetOrderStageIndex())
	{
	case 1:
		return TEXT("基础汉堡训练");
	case 2:
		return TEXT("沙拉切配");
	case 3:
		return TEXT("生菜汉堡进阶");
	case 4:
		return TEXT("番茄切配");
	case 5:
		return TEXT("厚肉煎制");
	default:
		return TEXT("豪华双肉挑战");
	}
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

	switch (GetOrderStageIndex())
	{
	case 1:
		return FString::Printf(TEXT("%s；先稳定完成 2 单经典汉堡"), *ScoreGoal);
	case 2:
		return FString::Printf(TEXT("%s；切生菜和番茄做田园沙拉"), *ScoreGoal);
	case 3:
		return FString::Printf(TEXT("%s；把切好的生菜加入汉堡"), *ScoreGoal);
	case 4:
		return FString::Printf(TEXT("%s；切番茄，注意不要换顺序"), *ScoreGoal);
	case 5:
		return FString::Printf(TEXT("%s；煎熟牛肉再提交厚肉堡"), *ScoreGoal);
	default:
		return FString::Printf(TEXT("%s；完成豪华双肉堡冲三星"), *ScoreGoal);
	}
}

FString UVRKitchenGameSessionComponent::GetTutorialHintText() const
{
	if (bSessionEnded)
	{
		return bMissionCleared
			? TEXT("挑战完成：复盘最佳连击，按 R 可以再跑一局。")
			: TEXT("时间到：按 R 重开，优先保持正确率。");
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
		Prefix = TEXT("刚才出错：先看红色失败原因。\n");
	}

	switch (GetOrderStageIndex())
	{
	case 1:
		return Prefix + TEXT("经典汉堡：底部面包 + 熟肉饼 + 顶部面包。");
	case 2:
		return Prefix + TEXT("田园沙拉：切好生菜和番茄后直接叠盘出餐，不需要煎锅。");
	case 3:
		return Prefix + TEXT("生菜汉堡：先切生菜，再放到熟肉饼上方。");
	case 4:
		return Prefix + TEXT("番茄汉堡：先切番茄，叠盘顺序仍然严格。");
	case 5:
		return Prefix + TEXT("厚肉生菜堡：使用熟牛肉，不要提交生肉或烧焦肉。");
	default:
		return Prefix + TEXT("豪华双肉堡：肉饼、生菜、熟牛肉、番茄都要按订单顺序。");
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
		TEXT("剩余时间: %02d:%02d  %s\n阶段: %s\n分数: %d / 目标: %d\n完成: %d  错误: %d  连击: %d\n下一目标: %s\n%s"),
		Minutes,
		Seconds,
		*GetUrgencyText(),
		*GetOrderStageText(),
		SessionScore,
		TargetScore,
		CorrectOrders,
		WrongOrders,
		CurrentStreak,
		*GetNextGoalText(),
		*LastFeedbackMessage);
}

FString UVRKitchenGameSessionComponent::BuildTutorialText() const
{
	return FString::Printf(
		TEXT("玩法提示\n%s\n步骤: 看订单 -> 切菜/煎肉 -> 按顺序叠盘 -> 出餐\n连续正确 3 单有奖励"),
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
