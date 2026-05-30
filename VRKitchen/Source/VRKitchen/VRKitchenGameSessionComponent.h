#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "TimerManager.h"
#include "VRKitchenGameSessionComponent.generated.h"

class UTextRenderComponent;

UCLASS(ClassGroup = (VRKitchen), meta = (BlueprintSpawnableComponent))
class VRKITCHEN_API UVRKitchenGameSessionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UVRKitchenGameSessionComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	double SessionLengthSeconds = 180.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	int32 CorrectOrderScore = 10;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	int32 WrongOrderPenalty = 2;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	int32 TargetScore = 115;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	int32 OneStarScore = 30;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	int32 TwoStarScore = 55;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	int32 ThreeStarScore = 115;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	double WarningTimeSeconds = 45.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	double CriticalTimeSeconds = 20.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	int32 StreakBonusEvery = 3;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	int32 StreakBonusScore = 5;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "VRKitchen|Session")
	bool bAutoStart = true;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	double RemainingSeconds = 0.0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	int32 SessionScore = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	int32 CorrectOrders = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	int32 WrongOrders = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	int32 CurrentStreak = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	int32 BestStreak = 0;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	FString LastFeedbackMessage;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	bool bSessionActive = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	bool bSessionEnded = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	bool bMissionCleared = false;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void StartSession();

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void ResetSession();

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void EndSession();

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void CompleteSession();

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	bool CanAcceptOrders() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void RecordOrderSubmission(bool bWasCorrect, const FString& FeedbackMessage);

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void ApplyDemoOrderForProgress();

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	int32 GetStarRating() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetResultTitle() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetResultGradeText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	int32 GetTotalOrderAttempts() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	int32 GetAccuracyPercent() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetAccuracyText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetMistakeSummaryText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetNextRunFocusText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetPerformanceSummaryText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	int32 GetMenuRouteTotal() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	int32 GetCurrentMenuRouteStep() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentMenuItemText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetMenuRouteText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	bool IsDemoMenuRouteHealthy() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetDemoMenuRouteQualityReportText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetMenuProgressText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentStageUnlockText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	int32 GetCorrectOrdersUntilNextStage() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetNextStagePreviewText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetLearningPathText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetStageCoachingText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentRequiredIngredientsText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentActionStepText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentStationRouteText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentStationOutcomeText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentDishTypeText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentRecipeProcessText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentRecipeAssemblyText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentRecipeWarningText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentRecipeCardText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentOrderBoardText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetCurrentPreSubmitChecklistText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetFailureRecoveryText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetPlayerObjectiveText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	int32 GetOrderStageIndex() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetOrderStageText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	int32 GetUrgencyLevel() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetUrgencyText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetNextGoalText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetTutorialHintText() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	FString GetTutorialText() const;

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	UPROPERTY(Transient)
	TObjectPtr<UTextRenderComponent> StatusTextComponent;

	UPROPERTY(Transient)
	TObjectPtr<UTextRenderComponent> TutorialTextComponent;

	FTimerHandle InitialOrderTimerHandle;

	void EnsureTextComponents();
	void UpdateStatusText();
	FString BuildStatusText() const;
	FString BuildTutorialText() const;
	FColor GetStatusTextColor() const;
};
