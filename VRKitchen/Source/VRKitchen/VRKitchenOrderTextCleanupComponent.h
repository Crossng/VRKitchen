#pragma once

#include "Components/ActorComponent.h"

#include "VRKitchenOrderTextCleanupComponent.generated.h"

UCLASS(ClassGroup=(VRKitchen), meta=(BlueprintSpawnableComponent))
class VRKITCHEN_API UVRKitchenOrderTextCleanupComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UVRKitchenOrderTextCleanupComponent();

protected:
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	void CleanupTempIngredientsText() const;
};
