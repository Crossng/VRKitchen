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
	bool bSessionActive = false;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "VRKitchen|Session")
	bool bSessionEnded = false;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void StartSession();

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void ResetSession();

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void EndSession();

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	bool CanAcceptOrders() const;

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void RecordOrderSubmission(bool bWasCorrect, const FString& FeedbackMessage);

	UFUNCTION(BlueprintCallable, Category = "VRKitchen|Session")
	void ApplyDemoOrderForProgress();

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
};
