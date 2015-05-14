package com.java2novoice;

public class SumOfDigitOfNo {
	static int sum=0;
	public static void main(String[] args) {
		sumOfDigits(153453);
		System.out.println(sum);
	}

	static void sumOfDigits(int num){
		if(num==0){
			
		}else{
			sum += num%10;
			num = num/10;
			sumOfDigits(num);
		}
	}
	
}
