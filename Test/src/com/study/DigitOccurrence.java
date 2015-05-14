package com.study;

// IMPORT LIBRARY PACKAGES NEEDED BY YOUR PROGRAM
// SOME CLASSES WITHIN A PACKAGE MAY BE RESTRICTED
// DEFINE ANY CLASS AND METHOD NEEDED
// CLASS BEGINS, THIS CLASS IS REQUIRED
public class DigitOccurrence {
	// METHOD SIGNATURE BEGINS, THIS METHOD IS REQUIRED
	public static int findDigitOccurrence(int num1, int num2) {
		// Check whether word1 and word2 are cyclic.
		// INSERT YOUR CODE HERE
		int count = 0;
		int temp1 = 0;
/*		while (num2 != 0) {
			temp1 = num2 % 10;

			num2 = num2 / 10;
			if (temp1 == num1) {
				count++;
			}
		}*/
		
		while (num2 >0){
			temp1 = num2 % 10;
			if(temp1 == num1)
				count++;
			num2 = num2/10;
		}
		
		return count;
	}

	// METHOD SIGNATURE ENDS

	// DO NOT IMPLEMENT THE main( ) METHOD
	public static void main(String[] args) {
		// PLEASE DO NOT MODIFY THIS FUNCTION
		// YOUR FUNCTION SHALL BE AUTOMATICALLY CALLED
		// AND THE INPUTS FROM HERE SHALL BE PASSED TO IT

		/*int digit = 9, num = 99, result;
		// ASSUME INPUTS HAVE ALREADY BEEN TAKEN
		result = findDigitOccurrence(digit, num);
		System.out.println(result);*/
		
		int n =5;
		/*int temp;
		for (int i=0; i<n; i++)
		{
			temp = i+1;
			for (int k=0;k<temp;k++)
			{
				System.out.print(temp);
			}
			System.out.println();
		}
		*/
		
		 int rows=n;
		 for(int i=0;i<n;i++)
		 {
		 System.out.print(i+1);
		 for(int j=0;j<i;j++)
		 {
		 int temp=i+1;
		 System.out.print("*"+temp);
		 }
		 System.out.println();}
	}
}
