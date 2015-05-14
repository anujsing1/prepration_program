package com.study;

public class Bitwise {

	public static void main(String[] args) {
		int number = 8; //0000 1000
	     System.out.println("Original number : " + number);
	   
	     //left shifting bytes with 1 position
	     number = number<<1; //should be 16 i.e. 0001 0000

	     //equivalent of multiplication of 2
	     System.out.println("value of number after left shift: " + number);
	     
	     //left shifting bytes with 1 position
	     number = number<<2; //should be 16 i.e. 0001 0000

	     //equivalent of multiplication of 2
	     System.out.println("value of number after left shift: " + number);
	   
	     number = -8;
	     //right shifting bytes with sign 1 position
	     number = number>>1; //should be 16 i.e. 0001 0000

	     //equivalent of division of 2
	     System.out.println("value of number after right shift with sign: " + number);
	   
	     number = -1;
	     //right shifting bytes without sign 1 position
	     number = number>>>1; //should be 16 i.e. 0001 0000

	     //equivalent of division of 2
	     System.out.println("value of number after right shift with sign: " + number);

	}

}
