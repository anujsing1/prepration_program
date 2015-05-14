/**
 * 
 */
package com.java2novoice;

import java.util.ArrayList;
import java.util.List;

/**
 * @author govind.gupta
 *
 */
public class DuplicateNumber {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		
		DuplicateNumber dn = new DuplicateNumber();
        List<Integer> numbers = new ArrayList<Integer>();
        for(int i=1;i<15;i++){
            numbers.add(i);
        }
        //add duplicate number into the list
        numbers.add(10);
        System.out.println(dn.findDuplicateNumber(numbers));
	}

	
    public int findDuplicateNumber(List<Integer> numbers){
        
        int highestNumber = numbers.size() - 1;
        int total = getSum(numbers);
        int duplicate = total - (highestNumber*(highestNumber+1)/2);
        return duplicate;
    }
     
    public int getSum(List<Integer> numbers){
         
        int sum = 0;
        for(int num:numbers){
            sum += num;
        }
        return sum;
    }
	
}
