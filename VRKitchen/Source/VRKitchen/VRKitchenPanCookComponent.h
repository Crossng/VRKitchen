#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "VRKitchenPanCookComponent.generated.h"

UCLASS(ClassGroup = (VRKitchen), meta = (BlueprintSpawnableComponent))
class VRKITCHEN_API UVRKitchenPanCookComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UVRKitchenPanCookComponent();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Cooking")
	double CookTimeSeconds = 3.0;

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
};
