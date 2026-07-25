(* ========================================================================= *)
(* SVM_Semantics.v                                                            *)
(* Formal Operational Semantics of IntentOS Semantic Virtual Machine (SVM)    *)
(* ========================================================================= *)

Require Import Coq.Lists.List.
Require Import Coq.Init.Nat.
Require Import Coq.Arith.PeanoNat.
Import ListNotations.

(* Define Address/Variable Space and Value Space *)
Definition Addr := nat.
Definition Val := nat.

(* Memory is modeled as a state function mapping Address to Value *)
Definition Mem := Addr -> Val.

(* Initial empty memory (all addresses map to 0) *)
Definition empty_mem : Mem := fun _ => 0.

(* Memory update helper *)
Definition update_mem (m : Mem) (a : Addr) (v : Val) : Mem :=
  fun x => if x =? a then v else m x.

(* IntentOS SVM core instructions *)
Inductive Instruction : Type :=
  | READ  : Addr -> Instruction          (* Read from memory address *)
  | WRITE : Addr -> Val -> Instruction   (* Write value to memory address *)
  | IF    : Addr -> list Instruction -> list Instruction -> Instruction (* Conditional branching *)
  | CALL  : Addr -> Instruction.         (* Subroutine invocation or jump to sub-task *)

Definition Program := list Instruction.

(* SVM State: Program Counter, Memory State, Gas/Fuel left *)
Record State : Type := mkState {
  pc : nat;
  mem : Mem;
  gas : nat
}.

(* Operational Semantics - Small-Step State Transitions *)
Inductive step : Program -> State -> State -> Prop :=
  | Step_Read : forall p s pc' g a,
      gas s = g ->
      g > 0 ->
      nth_error p (pc s) = Some (READ a) ->
      pc' = S (pc s) ->
      step p s (mkState pc' (mem s) (pred g))

  | Step_Write : forall p s pc' g a v m',
      gas s = g ->
      g > 0 ->
      nth_error p (pc s) = Some (WRITE a v) ->
      m' = update_mem (mem s) a v ->
      pc' = S (pc s) ->
      step p s (mkState pc' m' (pred g))

  | Step_If_True : forall p s pc' g a insts_t insts_f,
      gas s = g ->
      g > 0 ->
      nth_error p (pc s) = Some (IF a insts_t insts_f) ->
      (mem s) a <> 0 ->
      pc' = S (pc s) ->
      step p s (mkState pc' (mem s) (pred g))

  | Step_If_False : forall p s pc' g a insts_t insts_f,
      gas s = g ->
      g > 0 ->
      nth_error p (pc s) = Some (IF a insts_t insts_f) ->
      (mem s) a = 0 ->
      pc' = S (pc s) ->
      step p s (mkState pc' (mem s) (pred g))

  | Step_Call : forall p s pc' g a,
      gas s = g ->
      g > 0 ->
      nth_error p (pc s) = Some (CALL a) ->
      pc' = (mem s) a ->
      step p s (mkState pc' (mem s) (pred g)).
