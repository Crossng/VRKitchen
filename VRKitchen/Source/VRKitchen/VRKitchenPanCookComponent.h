#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "VRKitchenPanCookComponent.generated.h"

class AActor;

UCLASS(ClassGroup = (VRKitchen), meta = (BlueprintSpawnableComponent))
class VRKITCHEN_API UVRKitchenPanCookComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UVRKitchenPanCookComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cooking")
	double CookTimeSeconds = 3.0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cooking")
	double OvercookTimeSeconds = 4.0;

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	TMap<TWeakObjectPtr<AActor>, double> OvercookTimes;
};
