package com.java2novoice;

public class DecimalToBinary {

	public static void main(String[] args) {
		ConvertToBinary(16);
	}

	
	static void ConvertToBinary(int num) {
		int[] binary = new int[25];
		int index=0;
		while(num>0){
			binary[index] = num%2;
			num = num/2;
			index++;
		}
		for(int i = index-1;i >= 0;i--){
            System.out.print(binary[i]);
        }
	}
}
